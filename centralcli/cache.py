from typing import Union, List, Tuple
from aiohttp.client import ClientSession
from tinydb import TinyDB, Query
# from centralcli.central import CentralApi
from centralcli import log, utils, config

import asyncio
import time
import typer


class Cache:
    def __init__(self,  session=None, data: Union[List[dict, ], dict] = None, refresh: bool = False) -> None:
        self.updated: list = []
        self.session = session
        self.DevDB = TinyDB(config.cache_file)
        self.SiteDB = self.DevDB.table("sites")
        self.GroupDB = self.DevDB.table("groups")
        self.TemplateDB = self.DevDB.table("templates")
        self.MetaDB = self.DevDB.table("_metadata")
        self._tables = [self.DevDB, self.SiteDB, self.GroupDB, self.TemplateDB]
        self.Q = Query()
        if data:
            self.insert(data)
        if session:
            self.check_fresh(refresh)

    def __call__(self, refresh=False) -> None:
        if refresh:
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

    @property
    def prev_acct(self) -> str:
        return self.MetaDB.get(doc_id=1).get("prev_account")

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
        # start = time.time()
        # print(f" dev db start: {start}")
        resp = await self.session.get_all_devicesv2()
        # async with self.session.get_all_devicesv2() as resp:
        # resp = await self.session.get_all_devicesv2()
        if resp.ok:
            resp.output = utils.listify(resp.output)
            self.updated.append(self.session.get_all_devicesv2)
            self.DevDB.truncate()
            # print(f" dev db Done: {time.time() - start}")
            return self.DevDB.insert_multiple(resp.output)

    async def update_site_db(self):
        # start = time.time()
        # print(f" site db start: {start}")
        resp = await self.session.get_all_sites()
        # async with self.session.get_all_sites() as resp:
        # resp = await self.session.get_all_sites()
        if resp.ok:
            resp.output = utils.listify(resp.output)
            # TODO time this to see which is more efficient
            # upd = [self.SiteDB.upsert(site, cond=self.Q.id == site.get("id")) for site in site_resp.output]
            # upd = [item for in_list in upd for item in in_list]
            self.updated.append(self.session.get_all_sites)
            self.SiteDB.truncate()
            # print(f" site db Done: {time.time() - start}")
            return self.SiteDB.insert_multiple(resp.output)

    async def update_group_db(self):
        # start = time.time()
        # print(f" group db start: {start}")
        # async with self.session.get_all_groups() as resp:
        # resp = await self.session.get_all_groups()
        resp = await self.session.get_all_groups()
        if resp.ok:
            resp.output = utils.listify(resp.output)
            self.updated.append(self.session.get_all_groups)
            self.GroupDB.truncate()
            # print(f" group db Done: {time.time() - start}")
            return self.GroupDB.insert_multiple(resp.output)

    async def update_template_db(self):
        # start = time.time()
        # print(f" template db start: {start}")
        # async with self.session.get_all_groups() as resp:
        # resp = await self.session.get_all_groups()
        groups = self.groups if self.session.get_all_groups in self.updated else None
        resp = await self.session.get_all_templates(groups=groups)
        if resp.ok:
            resp.output = utils.listify(resp.output)
            self.updated.append(self.session.get_all_templates)
            self.TemplateDB.truncate()
            # print(f" template db Done: {time.time() - start}")
            return self.TemplateDB.insert_multiple(resp.output)

    def update_meta_db(self):
        self.MetaDB.truncate()
        return self.MetaDB.insert({"prev_account": config.account, "forget": time.time() + 7200})

    async def _check_fresh(self, dev_db: bool = False, site_db: bool = False, template_db: bool = False):
        async with ClientSession() as self.session.aio_session:
            if dev_db:
                await asyncio.gather(self.update_dev_db())
            elif site_db:
                await asyncio.gather(self.update_site_db())
            elif template_db:
                await asyncio.gather(self.update_template_db())

            # update groups first so template update can use the result, and to trigger token_refresh if necessary
            elif await self.update_group_db():
                await asyncio.gather(self.update_dev_db(), self.update_site_db(), self.update_template_db())

    def check_fresh(
        self, refresh: bool = False,
        site_db: bool = False, dev_db: bool = False, template_db: bool = False
    ):
        if refresh or not config.cache_file.is_file() or not config.cache_file.stat().st_size > 0 \
           or time.time() - config.cache_file.stat().st_mtime > 7200:
            start = time.time()
            typer.secho("-- Refreshing Identifier mapping Cache --", fg="cyan")
            asyncio.run(self._check_fresh(dev_db=dev_db, site_db=site_db, template_db=template_db))
            # loop = asyncio.get_event_loop()
            # try:
            #     loop.run_until_complete(self._check_fresh(dev_db=dev_db, site_db=site_db, template_db=template_db))
            #     loop.run_until_complete(loop.shutdown_asyncgens())
            # finally:
            #     loop.close()
            log.info(f"Cache Refreshed in {round(time.time() - start, 2)} seconds")
            typer.secho(f"-- Cache Refresh Completed in {round(time.time() - start, 2)} sec --", fg="cyan")

    def handle_multi_match(self, match: list, query_str: str = None, query_type: str = 'device') -> list:
        typer.secho(f" -- Ambiguos identifier provided.  Please select desired {query_type}. --\n", color="cyan")
        if query_type == 'site':
            fields = ('name', 'city', 'state', 'type')
        else:
            fields = ('name', 'serial', 'mac')
        menu = f"{' ':{len(str(len(match)))}}  {fields[0]:29} {fields[1]:12} {fields[2]:12} type"
        menu += f"\n{' ':{len(str(len(match)))}}  {'-' * 29} {'-' * 12} {'-' * 18} -------\n"
        menu += "\n".join(list(f'{idx + 1}. {m.get(fields[0], "error"):29} {m.get(fields[1], "error"):12} '
                               f'{m.get(fields[2], "error"):18} {m.get("type", "-")}' for idx, m in enumerate(match)))
        if query_str:
            menu = menu.replace(query_str, typer.style(query_str, fg='green'))
            menu = menu.replace(query_str.upper(), typer.style(query_str.upper(), fg='green'))
        typer.echo(menu)
        selection = ''
        valid = [str(idx + 1) for idx, _ in enumerate(match)]
        try:
            while selection not in valid:
                selection = typer.prompt(f'Select {query_type.title()}')
                if selection not in valid:
                    typer.secho(f"Invalid selection {selection}, try again.")
        except KeyboardInterrupt:
            raise typer.Abort()
        finally:
            return [match.pop(int(selection) - 1)]

    # TODO trigger update if no match is found and db wasn't updated recently
    # TODO create and return a device object so dev.serial dev.name etc can be used in prompts
    def get_dev_identifier(self,
                           query_str: Union[str, List[str], Tuple[str, ...]],
                           dev_type: str = None,
                           ret_field: str = "serial",
                           retry: bool = True
                           ) -> Union[str, Tuple]:

        # TODO dev_type currently not passed in or handled identifier for show switches would also
        # try to match APs ...  & (self.Q.type == dev_type)
        # TODO refactor to single test function usable by all identifier methods 1 search with a more involved test
        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)

        match = None
        for _ in range(0, 2 if retry else 1):
            # Try exact match
            match = self.DevDB.search((self.Q.name == query_str) | (self.Q.ip == query_str)
                                      | (self.Q.mac == utils.Mac(query_str).cols) | (self.Q.serial == query_str))

            # retry with case insensitive name match if no match with original query
            if not match:
                match = self.DevDB.search((self.Q.name.test(lambda v: v.lower() == query_str.lower()))
                                          | self.Q.mac.test(lambda v: v.lower() == utils.Mac(query_str).cols.lower())
                                          | self.Q.serial.test(lambda v: v.lower() == query_str.lower()))

            # retry name match swapping - for _ and _ for -
            if not match:
                if '-' in query_str:
                    match = self.DevDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("-", "_")))
                elif '_' in query_str:
                    match = self.DevDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("_", "-")))

            # Last Chance try to match name if it startswith provided value
            if not match:
                match = self.DevDB.search(self.Q.name.test(lambda v: v.lower().startswith(query_str.lower()))
                                          | self.Q.serial.test(lambda v: v.lower().startswith(query_str.lower()))
                                          | self.Q.mac.test(lambda v: v.lower().startswith(utils.Mac(query_str).cols.lower())))

            if retry and not match and self.session.get_all_devicesv2 not in self.updated:
                typer.secho(f"No Match Found for {query_str}, Updating Device Cachce", fg="red")
                self.check_fresh(refresh=True, dev_db=True)
            if match:
                break

        # TODO if multiple matches prompt for input or show both (with warning that data was from cahce)
        if match:
            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str)

            if ret_field == "type-serial":
                return match[0].get("type"), match[0].get("serial")
            else:
                return match[0].get(ret_field)
        elif retry:
            log.error(f"Unable to gather device {ret_field} from provided identifier {query_str}", show=True)
            raise typer.Abort()

    def get_site_identifier(self, query_str: Union[str, List[str], Tuple[str, ...]],
                            ret_field: str = "id", retry: bool = True) -> str:
        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)

        match = None
        for _ in range(0, 2 if retry else 1):
            # try exact site match
            match = self.SiteDB.search(
                (self.Q.name == query_str) | (self.Q.id.test(lambda v: str(v) == query_str))
                | (self.Q.zipcode == query_str) | (self.Q.address == query_str)
                | (self.Q.city == query_str) | (self.Q.state == query_str)
            )

            # retry with case insensitive name & address match if no match with original query
            if not match:
                match = self.SiteDB.search(
                    (self.Q.name.test(lambda v: v.lower() == query_str.lower()))
                    | self.Q.address.test(
                        lambda v: v.lower().replace(" ", "") == query_str.lower().replace(" ", "")
                    )
                )

            # retry name match swapping - for _ and _ for -
            if not match:
                if '-' in query_str:
                    match = self.SiteDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("-", "_")))
                elif '_' in query_str:
                    match = self.SiteDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("_", "-")))

            # Last Chance try to match name if it startswith provided value
            if not match:
                match = self.SiteDB.search(self.Q.name.test(lambda v: v.lower().startswith(query_str.lower())))

            if retry and not match and self.session.get_all_sites not in self.updated:
                typer.secho(f"No Match Found for {query_str}, Updating Site Cachce", fg="red")
                self.check_fresh(refresh=True, site_db=True)
            if match:
                break

        # TODO if multiple matches prompt for input or show both (with warning that data was from cahce)
        if match:
            if len(match) > 1:
                # TODO update to accomodate sites handle_multi_match formatted for devs
                match = self.handle_multi_match(match, query_str=query_str, query_type='site')

            return match[0].get(ret_field)

        elif retry:
            log.error(f"Unable to gather site {ret_field} from provided identifier {query_str}", show=True)
            raise typer.Abort()

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
