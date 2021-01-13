from typing import Union, List, Tuple
from tinydb import TinyDB, Query
from centralcli.central import CentralApi
from centralcli import config, log, utils

import asyncio
import time
import typer


class Cache:
    def __init__(self,  session: CentralApi = None, data: Union[List[dict, ], dict] = None, refresh: bool = False):
        self.updated: list = []
        self.session = session
        self.DevDB = TinyDB(config.cache_file)
        self.SiteDB = self.DevDB.table("sites")
        self.GroupDB = self.DevDB.table("groups")
        self.TemplateDB = self.DevDB.table("templates")
        self._tables = [self.DevDB, self.SiteDB, self.GroupDB, self.TemplateDB]
        self.Q = Query()
        if data:
            self.insert(data)
        if session:
            self.check_fresh(refresh)

    def __iter__(self) -> list:
        for db in self._tables:
            yield db.name(), db.all()

    @property
    def devices(self) -> list:
        return self.DevDB.all()

    @property
    def sites(self) -> list:
        return self.SiteDB.all()

    @property
    def groups(self) -> list:
        return self.GroupDB.all()

    @property
    def group_names(self) -> list:
        return [g["name"] for g in self.GroupDB.all()]

    @property
    def templates(self) -> list:
        return self.TemplateDB.all()

    @property
    def all(self) -> dict:
        return {t.name: getattr(self, t.name) for t in self._tables}

    # TODO deprecated should be able to remove this method
    def insert(self, data: Union[List[dict, ], dict]) -> bool:
        _data = data
        if isinstance(data, list) and data:
            _data = data[1]

        table = self.DevDB
        if "zipcode" in _data.keys():
            table = self.SiteDB

        data = data if isinstance(data, list) else [data]
        ret = table.insert_multiple(data)

        return len(ret) == len(data)

    async def update_dev_db(self):
        start = time.time()
        print(f" dev db start: {start}")
        resp = self.session.get_all_devicesv2()
        # async with self.session.get_all_devicesv2() as resp:
        # resp = await self.session.get_all_devicesv2()
        if resp.ok:
            self.updated.append(self.session.get_all_devicesv2)
            self.DevDB.truncate()
            print(f" dev db Done: {time.time() - start}")
            return self.DevDB.insert_multiple(resp.output)

    async def update_site_db(self):
        start = time.time()
        print(f" site db start: {start}")
        resp = self.session.get_all_sites()
        # async with self.session.get_all_sites() as resp:
        # resp = await self.session.get_all_sites()
        if resp.ok:
            # TODO time this to see which is more efficient
            # upd = [self.SiteDB.upsert(site, cond=self.Q.id == site.get("id")) for site in site_resp.output]
            # upd = [item for in_list in upd for item in in_list]
            self.updated.append(self.session.get_all_sites)
            self.SiteDB.truncate()
            print(f" site db Done: {time.time() - start}")
            return self.SiteDB.insert_multiple(resp.output)

    async def update_group_db(self):
        start = time.time()
        print(f" group db start: {start}")
        # async with self.session.get_all_groups() as resp:
        # resp = await self.session.get_all_groups()
        resp = self.session.get_all_groups()
        if resp.ok:
            self.updated.append(self.session.get_all_groups)
            self.GroupDB.truncate()
            print(f" group db Done: {time.time() - start}")
            return self.GroupDB.insert_multiple(resp.output)

    async def update_template_db(self):
        start = time.time()
        print(f" template db start: {start}")
        # async with self.session.get_all_groups() as resp:
        # resp = await self.session.get_all_groups()
        groups = self.groups if self.session.get_all_groups in self.updated else None
        resp = self.session.get_all_templates(groups=groups)
        if resp.ok:
            self.updated.append(self.session.get_all_templates)
            self.TemplateDB.truncate()
            print(f" template db Done: {time.time() - start}")
            return self.TemplateDB.insert_multiple(resp.output)

    async def _check_fresh(self):
        await asyncio.gather(self.update_dev_db(), self.update_site_db(), self.update_group_db(), self.update_template_db())

    def check_fresh(self, refresh: bool = False):
        if refresh or not config.cache_file.is_file() or not config.cache_file.stat().st_size > 0 \
           or time.time() - config.cache_file.stat().st_mtime > 7200:
            typer.secho("-- Refreshing Identifier mapping Cache --", fg="cyan")
            # asyncio.run(self._check_fresh())
            loop = asyncio.get_event_loop()
            try:
                loop.run_until_complete(self._check_fresh())
                loop.run_until_complete(loop.shutdown_asyncgens())
            finally:
                loop.close()

    # TODO trigger update if no match is found and db wasn't updated recently
    def get_dev_identifier(self,
                           query_str: Union[str, List[str], Tuple[str, ...]],
                           ret_field: str = "serial") -> Union[str, Tuple]:

        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)

        match = self.DevDB.search((self.Q.name == query_str) | (self.Q.ip == query_str)
                                  | (self.Q.mac == utils.Mac(query_str).cols) | (self.Q.serial == query_str))

        # retry with case insensitive name match if no match with original query
        if not match:
            match = self.DevDB.search((self.Q.name.test(lambda v: v.lower() == query_str.lower()))
                                      | self.Q.mac.test(lambda v: v.lower() == utils.Mac(query_str).cols.lower())
                                      | self.Q.serial.test(lambda v: v.lower() == query_str.lower()))

        # TODO if multiple matches prompt for input or show both (with warning that data was from cahce)
        if match:
            if ret_field == "type-serial":
                return match[0].get("type"), match[0].get("serial")
            else:
                return match[0].get(ret_field)
        else:
            log.error(f"Unable to gather device {ret_field} from provided identifier {query_str}", show=True)

    def get_site_identifier(self, query_str: Union[str, List[str], Tuple[str, ...]], ret_field: str = "id") -> str:
        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)

        match = self.SiteDB.search((self.Q.site_name == query_str) | (self.Q.site_id.test(lambda v: str(v) == query_str))
                                   | (self.Q.zipcode == query_str) | (self.Q.address == query_str)
                                   | (self.Q.city == query_str) | (self.Q.state == query_str))

        # retry with case insensitive name & address match if no match with original query
        if not match:
            match = self.SiteDB.search((self.Q.site_name.test(lambda v: v.lower() == query_str.lower()))
                                       | self.Q.address.test(
                                           lambda v: v.lower().replace(" ", "") == query_str.lower().replace(" ", "")
                                           )
                                       )

        if match:
            return match[0].get(ret_field)
        else:
            log.error(f"Unable to gather site {ret_field} from provided identifier {query_str}", show=True)

    def get_group_identifier(self, query_str: str, ret_field: str = "name") -> str:
        """Allows Case insensitive group match"""
        match = self.GroupDB.search((self.Q.name == query_str) | self.Q.name.test(lambda v: v.lower() == query_str.lower()))
        if match:
            return match[0].get(ret_field)
        else:
            log.error(f"Unable to gather group {ret_field} from provided identifier {query_str}", show=True)
            valid_groups = '\n'.join(self.group_names)
            typer.secho(f"{query_str} appears to be invalid", fg="red")
            typer.secho(f"Valid Groups:\n--\n{valid_groups}\n--\n", fg="cyan")

    def get_template_identifier(self, query_str: str, ret_field: str = "name") -> Union[str, Tuple]:
        """Allows case insensitive template match by template name"""
        match = self.TemplateDB.search((self.Q.name == query_str) | self.Q.name.test(lambda v: v.lower() == query_str.lower()))
        if match:
            if ret_field == "name":
                return match[0].get(ret_field)
            else:  # 'group-name' only other option
                return match[0].get("group"), match[0].get("name")
        else:
            log.error(f"Unable to gather template {ret_field} from provided identifier {query_str}", show=True)
