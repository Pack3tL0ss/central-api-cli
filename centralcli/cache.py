#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any, Literal, Dict, Union, List
from aiohttp.client import ClientSession
from tinydb import TinyDB, Query
from centralcli import log, utils, config

import asyncio
import time
import typer

try:
    import readline  # noqa imported for backspace support during prompt.
except Exception:
    pass

TinyDB.default_table_name = "devices"

DBType = Literal["dev", "site", "template", "group"]


class CentralObject:
    def __init__(self, db: DBType, data: Union[list, Dict[str, Any]]) -> Union[list, Dict[str, Any]]:
        self.is_dev, self.is_template, self.is_group, self.is_site = False, False, False, False
        data = None if not data else data
        setattr(self, f"is_{db}", True)

        if isinstance(data, list):
            if len(data) > 1:
                raise ValueError(f"CentralObject expects a single item presented with list of {len(data)}")
            elif data:
                data = data[0]

        self.data = data

    def __bool__(self):
        return bool(self.data)

    def __repr__(self):
        return f"<{self.__module__}.{type(self).__name__} ({bool(self)}) object at {hex(id(self))}>"

    def __str__(self):
        if isinstance(self.data, dict):
            return "\n".join([f"  {k}: {v}" for k, v in self.data.items()])

        return str(self.data)

    def __getitem__(self, key):
        return self.data[key]

    def __getattr__(self, name: str) -> Any:
        if hasattr(self, "data") and self.data:
            if name in self.data:
                return self.data[name]

        if hasattr(self, "data") and hasattr(self.data, name):
            return getattr(self.data, name)

        log.exception(f"Cache LookUp Failure: 'CentralObject' object has no attribute '{name}'", show=True)
        raise typer.Exit(1)


class Cache:
    def __init__(
        self,
        central=None,
        data: Union[
            List[
                dict,
            ],
            dict,
        ] = None,
        refresh: bool = False,
    ) -> None:
        self.updated: list = []
        self.central = central
        self.DevDB = TinyDB(config.cache_file)
        self.SiteDB = self.DevDB.table("sites")
        self.GroupDB = self.DevDB.table("groups")
        self.TemplateDB = self.DevDB.table("templates")
        # log db is used to provide simple index to get details for logs
        # vs the actual log id in form 'audit_trail_2021_2,AXfQAu2hkwsSs1O3R7kv'
        # it is updated anytime show logs is ran.
        self.LogDB = self.DevDB.table("logs")
        self._tables = [self.DevDB, self.SiteDB, self.GroupDB, self.TemplateDB]
        self.Q = Query()
        if data:
            self.insert(data)
        if central:
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
    def logs(self) -> list:
        return self.LogDB.all()

    @property
    def group_names(self) -> list:
        return [g["name"] for g in self.GroupDB.all()]

    @property
    def templates(self) -> list:
        return self.TemplateDB.all()

    @property
    def all(self) -> dict:
        return {t.name: getattr(self, t.name) for t in self._tables}

    # TODO ??deprecated?? should be able to remove this method. don't remember this note. looks used
    def insert(
        self,
        data: Union[
            List[
                dict,
            ],
            dict,
        ],
    ) -> bool:
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
        resp = await self.central.get_all_devicesv2()
        if resp.ok:
            resp.output = utils.listify(resp.output)
            self.updated.append(self.central.get_all_devicesv2)
            self.DevDB.truncate()
            return self.DevDB.insert_multiple(resp.output)

    async def update_site_db(self, data: Union[list, dict] = None, remove: bool = False) -> List[int]:
        # cli.cache.SiteDB.search(cli.cache.Q.id == del_list[0])[0].doc_id
        if data:
            data = utils.listify(data)
            if not remove:
                return self.SiteDB.insert_multiple(data)
            else:
                doc_ids = []
                for qry in data:
                    # provided list of site_ids to remove
                    if isinstance(qry, (int, str)) and str(qry).isdigit():
                        doc_ids += [self.SiteDB.get((self.Q.id == int(qry))).doc_id]
                    else:
                        # list of dicts with {search_key: value_to_search_for}
                        if len(qry.keys()) > 1:
                            raise ValueError(f"cache.update_site_db remove Should only have 1 query not {len(qry.keys())}")
                        q = list(qry.keys())[0]
                        doc_ids += [self.SiteDB.get((self.Q[q] == qry[q])).doc_id]
                return self.SiteDB.remove(doc_ids=doc_ids)
        else:
            resp = await self.central.get_all_sites()
            if resp.ok:
                resp.output = utils.listify(resp.output)
                # TODO time this to see which is more efficient
                # start = time.time()
                # upd = [self.SiteDB.upsert(site, cond=self.Q.id == site.get("id")) for site in site_resp.output]
                # upd = [item for in_list in upd for item in in_list]
                self.updated.append(self.central.get_all_sites)
                self.SiteDB.truncate()
                # print(f" site db Done: {time.time() - start}")
                return self.SiteDB.insert_multiple(resp.output)

    async def update_group_db(self, data: Union[list, dict] = None, remove: bool = False) -> List[int]:
        if data:
            data = utils.listify(data)
            if not remove:
                return self.GroupDB.insert_multiple(data)
            else:
                doc_ids = []
                for qry in data:
                    if len(qry.keys()) > 1:
                        raise ValueError(f"cache.update_group_db remove Should only have 1 query not {len(qry.keys())}")
                    q = list(qry.keys())[0]
                    doc_ids += [self.GroupDB.get((self.Q[q] == qry[q])).doc_id]
                return self.GroupDB.remove(doc_ids=doc_ids)
        else:
            resp = await self.central.get_all_groups()
            if resp.ok:
                resp.output = utils.listify(resp.output)
                self.updated.append(self.central.get_all_groups)
                self.GroupDB.truncate()
                return self.GroupDB.insert_multiple(resp.output)

    async def update_template_db(self):
        groups = self.groups if self.central.get_all_groups in self.updated else None
        resp = await self.central.get_all_templates(groups=groups)
        if resp.ok:
            resp.output = utils.listify(resp.output)
            self.updated.append(self.central.get_all_templates)
            self.TemplateDB.truncate()
            return self.TemplateDB.insert_multiple(resp.output)

    def update_log_db(self, log_data: List[Dict[str, Any]]) -> bool:
        self.LogDB.truncate()
        return self.LogDB.insert_multiple(log_data)

    async def _check_fresh(self, dev_db: bool = False, site_db: bool = False, template_db: bool = False, group_db: bool = False):
        update_funcs = []
        if dev_db:
            update_funcs += [self.update_dev_db]
        if site_db:
            update_funcs += [self.update_site_db]
        if template_db:
            update_funcs += [self.update_template_db]
        if group_db:
            update_funcs += [self.update_group_db]
        async with ClientSession() as self.central.aio_session:
            if update_funcs:
                if await update_funcs[0]():
                    if len(update_funcs) > 1:
                        await asyncio.gather(*[f() for f in update_funcs[1:]])

            # update groups first so template update can use the result, and to trigger token_refresh if necessary
            elif await self.update_group_db():
                await asyncio.gather(self.update_dev_db(), self.update_site_db(), self.update_template_db())

    def check_fresh(
        self,
        refresh: bool = False,
        site_db: bool = False,
        dev_db: bool = False,
        template_db: bool = False,
        group_db: bool = False,
    ) -> None:
        if True in [site_db, dev_db, group_db, template_db]:
            refresh = True

        if refresh or not config.cache_file.is_file() or not config.cache_file.stat().st_size > 0:
            #  or time.time() - config.cache_file.stat().st_mtime > 7200:
            start = time.time()
            print(typer.style("-- Refreshing Identifier mapping Cache --", fg="cyan"), end="")
            db_res = asyncio.run(self._check_fresh(dev_db=dev_db, site_db=site_db, template_db=template_db, group_db=group_db))
            if db_res and False in db_res:
                res_map = ["dev_db", "site_db", "template_db", "group_db"]
                res_map = ", ".join([db for idx, db in enumerate(res_map) if not db_res(idx)])
                log.error(f"TinyDB returned error ({res_map}) during db update")
                self.central.spinner.fail(f"Cache Refresh Returned an error updating ({res_map})")
            else:
                self.central.spinner.succeed(f"Cache Refresh Completed in {round(time.time() - start, 2)} sec")
            log.info(f"Cache Refreshed in {round(time.time() - start, 2)} seconds")
            # typer.secho(f"-- Cache Refresh Completed in {round(time.time() - start, 2)} sec --", fg="cyan")

    def handle_multi_match(
        self,
        match: list,
        query_str: str = None,
        query_type: str = "device",
        multi_ok: bool = False,
    ) -> List[Dict[str, Any]]:
        # typer.secho(f" -- Ambiguos identifier provided.  Please select desired {query_type}. --\n", color="cyan")
        typer.echo()
        if query_type == "site":
            fields = ("name", "city", "state", "type")
        elif query_type == "template":
            fields = ("name", "group", "model", "device_type", "version")
        else:  # device
            fields = ("name", "serial", "mac", "type")
        out = utils.output(
            [{k: d[k] for k in d if k in fields} for d in match],
            title=f"Ambiguos identifier. Select desired {query_type}."
        )
        menu = out.menu(data_len=len(match))

        if query_str:
            menu = menu.replace(query_str, typer.style(query_str, fg="green"))
            menu = menu.replace(query_str.upper(), typer.style(query_str.upper(), fg="green"))
        typer.echo(menu)
        selection = ""
        valid = [str(idx + 1) for idx, _ in enumerate(match)]
        try:
            while selection not in valid:
                selection = typer.prompt(f"Select {query_type.title()}")
                if not selection or selection not in valid:
                    typer.secho(f"Invalid selection {selection}, try again.")
        except KeyboardInterrupt:
            raise typer.Abort()

        return [match.pop(int(selection) - 1)]

    def get_identifier(
        self,
        qry_str: str,
        qry_funcs: tuple,
        device_type: str = None,
        group: str = None,
        multi_ok: bool = False,
    ) -> CentralObject:
        match = None
        default_kwargs = {"retry": False}
        for _ in range(0, 2):
            for q in qry_funcs:
                kwargs = default_kwargs.copy()
                if q == "dev":
                    kwargs["dev_type"] = device_type
                elif q == "template":
                    kwargs["group"] = group
                match: CentralObject = getattr(self, f"get_{q}_identifier")(qry_str, **kwargs)

                if match:
                    return match

            # No match found trigger refresh and try again.
            if not match:
                self.check_fresh(
                    dev_db=True if "dev" in qry_funcs else False,
                    site_db=True if "site" in qry_funcs else False,
                    template_db=True if "template" in qry_funcs else False,
                    group_db=True if "group" in qry_funcs else False,
                )

        if not match:
            typer.secho(f"Unable to find a matching identifier for {qry_str}, tried: {qry_funcs}", fg="red")
            raise typer.Exit(1)

    def get_dev_identifier(
        self,
        query_str: Union[str, List[str], tuple],
        dev_type: str = None,
        ret_field: str = "serial",
        retry: bool = True,
        multi_ok: bool = True,
    ) -> CentralObject:

        # TODO dev_type currently not passed in or handled identifier for show switches would also
        # try to match APs ...  & (self.Q.type == dev_type)
        # TODO refactor to single test function usable by all identifier methods 1 search with a more involved test
        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)

        match = None
        for _ in range(0, 2 if retry else 1):
            # Try exact match
            match = self.DevDB.search(
                (self.Q.name == query_str)
                | (self.Q.ip.test(lambda v: v.split("/")[0] == query_str))
                | (self.Q.mac == utils.Mac(query_str).cols)
                | (self.Q.serial == query_str)
            )

            # retry with case insensitive name match if no match with original query
            if not match:
                match = self.DevDB.search(
                    (self.Q.name.test(lambda v: v.lower() == query_str.lower()))
                    | self.Q.mac.test(lambda v: v.lower() == utils.Mac(query_str).cols.lower())
                    | self.Q.serial.test(lambda v: v.lower() == query_str.lower())
                )

            # retry name match swapping - for _ and _ for -
            if not match:
                if "-" in query_str:
                    match = self.DevDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("-", "_")))
                elif "_" in query_str:
                    match = self.DevDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("_", "-")))

            # Last Chance try to match name if it startswith provided value
            if not match:
                match = self.DevDB.search(
                    self.Q.name.test(lambda v: v.lower().startswith(query_str.lower()))
                    | self.Q.serial.test(lambda v: v.lower().startswith(query_str.lower()))
                    | self.Q.mac.test(lambda v: v.lower().startswith(utils.Mac(query_str).cols.lower()))
                )

            if retry and not match and self.central.get_all_devicesv2 not in self.updated:
                typer.secho(f"No Match Found for {query_str}, Updating Device Cache", fg="red")
                self.check_fresh(refresh=True, dev_db=True)
            if match:
                break

        all_match = None
        if dev_type:
            all_match = match
            match = [d for d in match if d["type"].lower() in "".join(dev_type[0:len(d["type"])]).lower()]

        if match:
            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str, multi_ok=multi_ok)

            return CentralObject("dev", match)
        elif retry:
            log.error(f"Unable to gather device {ret_field} from provided identifier {query_str}", show=True)
            if all_match:
                all_match = all_match[-1]
                log.error(
                    f"The Following device matched {all_match.get('name')} excluded as {all_match.get('type')} != {dev_type}",
                    show=True,
                )
            raise typer.Abort()
        # else:
        #     log.error(f"Unable to gather device {ret_field} from provided identifier {query_str}", show=True)

    def get_site_identifier(
        self,
        query_str: Union[str, List[str], tuple],
        ret_field: str = "id",
        retry: bool = True,
        multi_ok: bool = False,
    ) -> CentralObject:
        if isinstance(query_str, (list, tuple)):
            query_str = " ".join(query_str)

        match = None
        for _ in range(0, 2 if retry else 1):
            # try exact site match
            match = self.SiteDB.search(
                (self.Q.name == query_str)
                | (self.Q.id.test(lambda v: str(v) == query_str))
                | (self.Q.zipcode == query_str)
                | (self.Q.address == query_str)
                | (self.Q.city == query_str)
                | (self.Q.state == query_str)
            )

            # retry with case insensitive name & address match if no match with original query
            if not match:
                match = self.SiteDB.search(
                    (self.Q.name.test(lambda v: v.lower() == query_str.lower()))
                    | self.Q.address.test(lambda v: v.lower().replace(" ", "") == query_str.lower().replace(" ", ""))
                )

            # retry name match swapping - for _ and _ for -
            if not match:
                if "-" in query_str:
                    match = self.SiteDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("-", "_")))
                elif "_" in query_str:
                    match = self.SiteDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("_", "-")))

            # Last Chance try to match name if it startswith provided value
            if not match:
                match = self.SiteDB.search(self.Q.name.test(lambda v: v.lower().startswith(query_str.lower())))

            if retry and not match and self.central.get_all_sites not in self.updated:
                typer.secho(f"No Match Found for {query_str}, Updating Site Cache", fg="red")
                self.check_fresh(refresh=True, site_db=True)
            if match:
                break

        if match:
            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str, query_type="site", multi_ok=multi_ok)

            # return match[0].get(ret_field)
            return CentralObject("site", match)

        elif retry:
            log.error(f"Unable to gather site {ret_field} from provided identifier {query_str}", show=True)
            raise typer.Abort()

    def get_group_identifier(
        self,
        query_str: str,
        ret_field: str = "name",
        retry: bool = True,
        multi_ok: bool = False,
    ) -> CentralObject:
        """Allows Case insensitive group match"""
        for _ in range(0, 2):
            match = self.GroupDB.search((self.Q.name == query_str) | self.Q.name.test(lambda v: v.lower() == query_str.lower()))
            if retry and not match and self.central.get_all_groups not in self.updated:
                typer.secho(f"No Match Found for {query_str}, Updating group Cache", fg="red")
                self.check_fresh(refresh=True, group_db=True)
                _ += 1
            if match:
                break

        if match:
            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str, query_type="group", multi_ok=multi_ok)

            return CentralObject("group", match)
        elif retry:
            log.error(f"Unable to gather group {ret_field} from provided identifier {query_str}", show=True)
            valid_groups = "\n".join(self.group_names)
            typer.secho(f"{query_str} appears to be invalid", fg="red")
            typer.secho(f"Valid Groups:\n--\n{valid_groups}\n--\n", fg="cyan")
            raise typer.Abort()
        else:
            log.error(f"Unable to gather template {ret_field} from provided identifier {query_str}", show=True)

    def get_template_identifier(
        self,
        query_str: str,
        ret_field: str = "name",
        group: str = None,
        retry: bool = True,
        multi_ok: bool = False,
    ) -> CentralObject:
        """Allows case insensitive template match by template name"""
        match = None
        for _ in range(0, 2 if retry else 1):
            match = self.TemplateDB.search(
                (self.Q.name == query_str) | self.Q.name.test(lambda v: v.lower() == query_str.lower())
            )

            if not match:
                match = self.TemplateDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("_", "-")))

            if not match:
                match = self.TemplateDB.search(self.Q.name.test(lambda v: v.lower().startswith(query_str.lower())))

            if retry and not match and self.central.get_all_templates not in self.updated:
                typer.secho(f"No Match Found for {query_str}, Updating template Cache", fg="red")
                self.check_fresh(refresh=True, template_db=True)
            if match:
                break

        if match:
            if len(match) > 1:
                if group:
                    match = [{k: d[k] for k in d} for d in match if d["group"].lower() == group.lower()]

            if len(match) > 1:
                match = self.handle_multi_match(
                    match,
                    query_str=query_str,
                    query_type="template",
                    multi_ok=multi_ok,
                )

            return CentralObject("template", match)

        elif retry:
            log.error(f"Unable to gather template {ret_field} from provided identifier {query_str}", show=True)
            raise typer.Abort()
        else:
            log.warning(f"Unable to gather template {ret_field} from provided identifier {query_str}", show=False)

    def get_log_identifier(self, query: str) -> str:
        if "audit_trail" in query:
            return query

        try:

            match = self.LogDB.search(self.Q.id == int(query))
            if not match:
                log.warning(f"Unable to gather log id from short index query {query}", show=True)
                typer.echo("Short log_id aliases are built each time 'show logs' is ran.")
                typer.echo("  You can verify the cache by running (hidden command) 'show cache logs'")
                typer.echo("  run 'show logs [OPTIONS]' then use the short index for details")
                raise typer.Abort()
            else:
                return match[-1]["long_id"]

        except ValueError as e:
            log.exception(f"Exception in get_log_identifier {e.__class__.__name__}\n{e}")
            typer.secho(f"Exception in get_log_identifier {e.__class__.__name__}", fg="red")
            raise typer.Exit(1)
