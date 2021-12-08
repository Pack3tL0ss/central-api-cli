#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any, Literal, Dict, Sequence, Union, List
from aiohttp.client import ClientSession
from tinydb import TinyDB, Query
from centralcli import log, utils, config, CentralApi

import asyncio
import time
import typer

try:
    import readline  # noqa imported for backspace support during prompt.
except Exception:
    pass

# try:
#     import better_exceptions # noqa
# except Exception:
#     pass
from rich.traceback import install
install(show_locals=True)


TinyDB.default_table_name = "devices"

DBType = Literal["dev", "site", "template", "group"]
DEV_COMPLETION = ["move", "device", ""]
SITE_COMPLETION = ["site"]
GROUP_COMPLETION = ["group", "wlan"]
TEMPLATE_COMPLETION = []
EXTRA_COMPLETION = {
    "move": ["site", "group"]
}
LIB_DEV_TYPE = {
    "AOS-CX": "cx",
    "AOS-S": "sw",
    "gateway": "gw"
}


def get_cencli_devtype(dev_type: str) -> str:
    """Convert device type returned by API to consistent cencli types

    Args:
        dev_type(str): device type provided by API response

    Returns:
        str: One of ["ap", "sw", "cx", "gw"]
    """
    return LIB_DEV_TYPE.get(dev_type, dev_type)


class CentralObject:
    def __init__(
        self,
        db: Literal["dev", "site", "template", "group"],
        data: Union[list, Dict[str, Any]],
    ) -> Union[list, Dict[str, Any]]:
        self.is_dev, self.is_template, self.is_group, self.is_site = False, False, False, False
        data = None if not data else data
        setattr(self, f"is_{db}", True)
        self.cache = db

        if isinstance(data, list):
            if len(data) > 1:
                raise ValueError(f"CentralObject expects a single item presented with list of {len(data)}")
            elif data:
                data = data[0]

        self.data = data

    def __bool__(self):
        return bool(self.data)

    def __repr__(self):
        _ = f"<{self.__module__}.{type(self).__name__} ({self.cache}|{self.get('name', bool(self))}) object at {hex(id(self))}>"
        return _

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

    @property
    def generic_type(self):
        if "type" in self.data:
            return "switch" if self.data["type"].lower() in ["cx", "sw"] else self.data["type"].lower()

    @property
    def help_text(self):
        parts = []
        if self.cache == "site":
            parts = [
                "Site",
                *[a for a in [self.city, self.state, self.zipcode] if a]
            ]
        elif self.cache == "template":
            parts = [
                self.device_type,
                self.model,
                f"s:{self.group}",
            ]
        elif self.cache == "dev":
            parts = [
                self.generic_type.upper(),
                self.serial,
                self.mac,
                self.ip,
                f"s:{self.site}",
            ]

        return "|".join(
            [
                typer.style(p, fg="blue" if not idx % 2 == 0 else "cyan") for idx, p in enumerate(parts)
            ]
        )


class Cache:
    def __init__(
        self,
        central: CentralApi = None,
        data: Union[
            List[
                dict,
            ],
            dict,
        ] = None,
        refresh: bool = False,
    ) -> None:
        self.rl: str = ""  # TODO temp might refactor cache updates to return resp
        self.updated: list = []  # TODO change from list of methods to something easier
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

    @staticmethod
    def account_completion(incomplete: str,):
        for a in config.defined_accounts:
            if a.lower().startswith(incomplete.lower()):
                yield a

    def smg_kw_completion(self, incomplete: str, args: List[str] = []):
        kwds = ["group", "mac", "serial"]
        out = []
        if args[-1].lower() == "group":
            out = [m for m in self.group_completion(incomplete, args)]
            for m in out:
                yield m
        elif args[-1].lower() == "serial":
            # out = [m for m in self.serial_pfx_completion(incomplete, args)]
            out = ["|", "<SERIAL NUMBER>"]
            if incomplete:
                out.append(incomplete)
            for m in out:
                yield m
        elif args[-1].lower() == "mac":
            # out = [m for m in self.mac_oui_completion(incomplete, args)]
            out = ["|", "<MAC ADDRESS>"]
            for m in out:
                yield m

        else:
            # print(args[-2], incomplete)
            # if args[-2].lower() == "mac":
            #     # TODO not sure why but colons in prev arg breaks completion for next kw
            #     args[-1] = args[-1].strip(":-.")
            for kw in kwds:
                if kw not in args and kw.lower().startswith(incomplete):
                    yield kw

    def null_completion(self, incomplete: str, args: List[str] = None):
        incomplete = "NULL_COMPLETION"
        _ = incomplete
        for m in ["|", "<cr>"]:
            yield m

    def dev_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ):
        dev_type = None

        if args:
            if args[-1].lower() in ["gateways", "clients", "server"]:
                dev_type = "gw"
            elif args[-1].lower().startswith("switch"):
                dev_type = "switch"
            elif args[-1].lower() in ["aps", "ap"]:
                dev_type = "ap"

        match = self.get_dev_identifier(
            incomplete,
            dev_type=dev_type,
            completion=True,
        )
        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                if m.name.startswith(incomplete):
                    out += [tuple([m.name, m.help_text])]
                elif m.serial.startswith(incomplete):
                    out += [tuple([m.serial, m.help_text])]
                elif m.mac.strip(":.-").lower().startswith(incomplete.strip(":.-")):
                    out += [tuple([m.mac, m.help_text])]
                elif m.ip.startswith(incomplete):
                    out += [tuple([m.ip, m.help_text])]
                else:
                    # failsafe, shouldn't hit
                    out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    def dev_kwarg_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ):
        """Completion for commands that allow a list of devices followed by group/site.

        i.e. cencli move dev1 dev2 dev3 site site_name group group_name

        Args:
            incomplete (str): The incomplete word for autocompletion
            args (List[str], optional): The prev args passed into the command.

        Yields:
            tuple: matching completion string, help text
        """
        if args[-1].lower() == "group":
            out = [m for m in self.group_completion(incomplete, args)]
            for m in out:
                yield m

        elif args[-1].lower() == "site":
            out = [m for m in self.site_completion(incomplete, args)]
            for m in out:
                yield m

        else:
            out = []
            if len(args) > 1:
                if "site" not in args and "site".startswith(incomplete.lower()):
                    out += ("site", )
                if "group" not in args and "group".startswith(incomplete.lower()):
                    out += ("group", )

            if "site" not in args and "group" not in args:
                out += [m for m in self.dev_completion(incomplete, args)]
            elif "site" in args and "group" in args:
                incomplete = "NULL_COMPLETION"
                out += ["|", "<cr>"]

            for m in out:
                yield m

    def group_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ):
        match = self.get_group_identifier(
            incomplete,
            completion=True,
        )
        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m[0], m[1]

    def site_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ):
        match = self.get_site_identifier(
            incomplete.replace('"', "").replace("'", ""),
            completion=True,
        )
        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name if " " not in m.name else f"'{m.name}'", m.help_text])]

        for m in out:
            yield m

    def template_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ):
        match = self.get_template_identifier(
            incomplete,
            completion=True,
        )
        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    def dev_template_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ):
        match = self.get_template_identifier(
            incomplete,
            completion=True,
        )
        match = match or []
        dev_match = self.get_dev_identifier(
            incomplete,
            completion=True,
        )
        match += dev_match or []
        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    def dev_site_completion(
        self,
        incomplete: str,
        args: List[str] = None,
    ):
        match = self.get_dev_identifier(
            incomplete,
            completion=True,
        )
        match = match or []
        match += self.get_site_identifier(
            incomplete,
            completion=True,
        ) or []
        out = []
        if match:
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

    def remove_completion(
        self,
        incomplete: str,
        args: List[str],
    ):
        if args[-1].lower() == "site":
            out = [m for m in self.site_completion(incomplete)]
            for m in out:
                yield m
        else:
            out = []
            if len(args) > 1:
                if "site" not in args and "site".startswith(incomplete.lower()):
                    out += ("site", )

            if "site" not in args:
                out += [m for m in self.dev_completion(incomplete)]
            else:
                out += [m for m in self.null_completion(incomplete)]

            for m in out:
                yield m

    def completion(
        self,
        incomplete: str,
        args: List[str],
    ):
        cache = ()
        if [True for m in DEV_COMPLETION if args[-1].endswith(m)]:
            cache += tuple(["dev"])
        elif [True for m in GROUP_COMPLETION if args[-1].endswith(m)]:
            cache += tuple(["group"])
        elif [True for m in SITE_COMPLETION if args[-1].endswith(m)]:
            cache += tuple(["site"])
        elif [True for m in TEMPLATE_COMPLETION if args[-1].endswith(m)]:
            cache += tuple(["template"])

        if not cache:
            match = self.get_identifier(
                incomplete,
                ("dev", "group", "site", "template"),
                completion=True,
            )
        else:
            match = self.get_identifier(
                incomplete,
                tuple(cache),
                completion=True,
            )

        out = []
        _extra = [e for e in EXTRA_COMPLETION if e in args and args[-1] != e]
        if _extra:
            out += [
                tuple([m, "COMMAND KEYWORD"]) for e in _extra for m in EXTRA_COMPLETION[e]
                if m.startswith(incomplete) and args[-1] != m
                ]

        if match:
            for m in sorted(match, key=lambda i: i.name):
                out += [tuple([m.name, m.help_text])]

        for m in out:
            yield m

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

    # TODO have update methods return Response
    async def update_dev_db(self):
        resp = await self.central.get_all_devicesv2()
        if resp.ok:
            self.rl = str(resp.rl)
            resp.output = utils.listify(resp.output)
            resp.output = [
                {
                    k: v if k != "type" else get_cencli_devtype(v) for k, v in r.items()
                } for r in resp.output
            ]
            # TODO change updated from  list of funcs to class with bool attributes or something
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
        match: List[CentralObject],
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
            [{k: d[k] for k in d.data if k in fields} for d in match],
            title=f"Ambiguos identifier. Select desired {query_type}."
        )
        menu = out.menu(data_len=len(match))

        if query_str:
            menu = menu.replace(query_str, typer.style(query_str, fg="bright_cyan"))
            menu = menu.replace(query_str.upper(), typer.style(query_str.upper(), fg="bright_cyan"))
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
        qry_funcs: Sequence[str],
        device_type: str = None,
        group: str = None,
        multi_ok: bool = False,
        completion: bool = False,
    ) -> CentralObject:
        """Get Identifier when iden type could be one of multiple types.  i.e. device or group

        Args:
            qry_str (str): The query string provided by user.
            qry_funcs (Sequence[str]): Sequence of strings "dev", "group", "site", "template"
            device_type (str, optional): str indicating what devices types are valid for dev idens.
                Defaults to None.
            group (str, optional): applies to get_template_identifier, Only match if template is in this group.
                Defaults to None.
            multi_ok (bool, optional): DEPRECATED, NO LONGER USED
            completion (bool, optional): If function is being called for AutoCompletion purposes. Defaults to False.
                When called for completion it will fail silently and will return multiple when multiple matches are found.

        Raises:
            typer.Exit: If not ran for completion, and there is no match, exit with code 1.

        Returns:
            CentralObject
        """
        # TODO remove multi_ok once verified refs are removed
        match = None
        default_kwargs = {"retry": False, "completion": completion}
        for _ in range(0, 2):
            for q in qry_funcs:
                kwargs = default_kwargs.copy()
                if q == "dev":
                    kwargs["dev_type"] = device_type
                elif q == "template":
                    kwargs["group"] = group
                match: CentralObject = getattr(self, f"get_{q}_identifier")(qry_str, **kwargs)

                if match and not completion:
                    return match

            # No match found trigger refresh and try again.
            if not match and not completion:
                self.check_fresh(
                    dev_db=True if "dev" in qry_funcs else False,
                    site_db=True if "site" in qry_funcs else False,
                    template_db=True if "template" in qry_funcs else False,
                    group_db=True if "group" in qry_funcs else False,
                )

        if completion:
            return match

        if not match:
            typer.secho(f"Unable to find a matching identifier for {qry_str}, tried: {qry_funcs}", fg="red")
            raise typer.Exit(1)

    def get_dev_identifier(
        self,
        query_str: Union[str, List[str], tuple],
        dev_type: str = None,
        ret_field: str = "serial",       # TODO ret_field believe to be deprecated, now returns an object with all attributes
        retry: bool = True,
        multi_ok: bool = True,          # TODO multi_ok also believe to be deprecated check
        completion: bool = False,
    ) -> CentralObject:

        retry = False if completion else retry
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
                )
                if not match:
                    qry_mac = utils.Mac(query_str)
                    qry_mac_fuzzy = utils.Mac(query_str, fuzzy=True)
                    if qry_mac or len(qry_mac) == len(qry_mac_fuzzy):
                        match = self.DevDB.search(
                            self.Q.mac.test(lambda v: v.lower().startswith(utils.Mac(query_str, fuzzy=completion).cols.lower()))
                        )
            if retry and not match and self.central.get_all_devicesv2 not in self.updated:
                typer.secho(f"No Match Found for {query_str}, Updating Device Cache", fg="red")
                self.check_fresh(refresh=True, dev_db=True)
            if match:
                match = [CentralObject("dev", dev) for dev in match]

        all_match = None
        if dev_type:
            all_match = match
            match = [d for d in match if d.generic_type.lower() in "".join(dev_type[0:len(d.generic_type)]).lower()]

        if match:
            if completion:
                return match

            elif len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str, multi_ok=multi_ok)

            return match[0]
        elif retry:
            log.error(f"Unable to gather device {ret_field} from provided identifier {query_str}", show=True)
            if all_match:
                # all_match = all_match[-1]
                all_match_msg = f"{', '.join(m.name for m in all_match[0:5])}{', ...' if len(all_match) > 5 else ''}"
                log.error(
                    f"The Following devices matched {all_match_msg} excluded as device type != {dev_type}",
                    show=True,
                )
            raise typer.Exit(1)
        # else:
        #     log.error(f"Unable to gather device {ret_field} from provided identifier {query_str}", show=True)

    def get_site_identifier(
        self,
        query_str: Union[str, List[str], tuple],
        ret_field: str = "id",
        retry: bool = True,
        multi_ok: bool = False,
        completion: bool = False,
    ) -> CentralObject:
        retry = False if completion else retry
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

            # swap _ and - and case insensitive
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
                match = [CentralObject("site", s) for s in match]
                break

        if match:
            if completion:
                return match

            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str, query_type="site", multi_ok=multi_ok)

            return match[0]

        elif retry:
            log.error(f"Unable to gather site {ret_field} from provided identifier {query_str}", show=True)
            raise typer.Exit(1)

    def get_group_identifier(
        self,
        query_str: str,
        ret_field: str = "name",
        retry: bool = True,
        multi_ok: bool = False,
        completion: bool = False,
    ) -> CentralObject:
        """Allows Case insensitive group match"""
        retry = False if completion else retry
        for _ in range(0, 2):
            # Exact match
            match = self.GroupDB.search((self.Q.name == query_str))

            # case insensitive
            if not match:
                match = self.GroupDB.search(
                    self.Q.name.test(lambda v: v.lower() == query_str.lower())
                )

            # case insensitive ignore -_
            if not match:
                if "_" in query_str or "-" in query_str:
                    match = self.GroupDB.search(
                        self.Q.name.test(
                            lambda v: v.lower().strip("-_") == query_str.lower().strip("_-")
                        )
                    )
                #     match = self.GroupDB.search(
                #         self.Q.name.test(
                #             lambda v: v.lower() == query_str.lower().replace("_", "-")
                #         )
                #     )
                # elif "-" in query_str:
                #     match = self.GroupDB.search(
                #         self.Q.name.test(
                #             lambda v: v.lower() == query_str.lower().replace("-", "_")
                #         )
                #     )

            # case insensitive startswith
            if not match:
                match = self.GroupDB.search(
                    self.Q.name.test(lambda v: v.lower().startswith(query_str.lower()))
                )

            # case insensitive startswith ignore - _
            if not match:
                match = self.GroupDB.search(
                    self.Q.name.test(
                        lambda v: v.lower().strip("-_").startswith(query_str.lower().strip("-_"))
                    )
                )

            if not match and retry and self.central.get_all_groups not in self.updated:
                typer.secho(f"No Match Found for {query_str}, Updating group Cache", fg="red")
                self.check_fresh(refresh=True, group_db=True)
                _ += 1
            if match:
                match = [CentralObject("group", g) for g in match]
                break

        if match:
            if completion:
                return match

            if len(match) > 1:
                match = self.handle_multi_match(match, query_str=query_str, query_type="group", multi_ok=multi_ok)

            return match[0]

        elif retry:
            log.error(f"Central API CLI Cache unable to gather group data from provided identifier {query_str}", show=True)
            valid_groups = "\n".join(self.group_names)
            typer.secho(f"{query_str} appears to be invalid", fg="red")
            typer.secho(f"Valid Groups:\n--\n{valid_groups}\n--\n", fg="cyan")
            raise typer.Exit(1)
        else:
            if not completion:
                log.error(
                    f"Central API CLI Cache unable to gather group data from provided identifier {query_str}", show=True
                )

    def get_template_identifier(
        self,
        query_str: str,
        ret_field: str = "name",
        group: str = None,
        retry: bool = True,
        multi_ok: bool = False,
        completion: bool = False,
    ) -> CentralObject:
        """Allows case insensitive template match by template name"""
        retry = False if completion else retry
        match = None
        for _ in range(0, 2 if retry else 1):
            # exact
            match = self.TemplateDB.search(
                (self.Q.name == query_str)
            )

            # case insensitive
            if not match:
                match = self.TemplateDB.search(
                    self.Q.name.test(lambda v: v.lower() == query_str.lower())
                )

            # case insensitive with -/_ swap
            if not match:
                if "_" in query_str:
                    match = self.TemplateDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("_", "-")))
                elif "-" in query_str:
                    match = self.TemplateDB.search(self.Q.name.test(lambda v: v.lower() == query_str.lower().replace("-", "_")))

            # startswith
            if not match:
                match = self.TemplateDB.search(self.Q.name.test(lambda v: v.lower().startswith(query_str.lower())))

            if retry and not match and self.central.get_all_templates not in self.updated:
                typer.secho(f"No Match Found for {query_str}, Updating template Cache", fg="red")
                self.check_fresh(refresh=True, template_db=True)
            if match:
                match = [CentralObject("template", tmplt) for tmplt in match]
                break

        if match:
            if completion:
                return match

            if len(match) > 1:
                if group:
                    match = [d for d in match if d.group.lower() == group.lower()]

            if len(match) > 1:
                match = self.handle_multi_match(
                    match,
                    query_str=query_str,
                    query_type="template",
                    multi_ok=multi_ok,
                )

            return match[0]

        elif retry:
            log.error(f"Unable to gather template {ret_field} from provided identifier {query_str}", show=True)
            raise typer.Exit(1)
        else:
            if not completion:
                log.warning(f"Unable to gather template {ret_field} from provided identifier {query_str}", show=False)

    def get_log_identifier(self, query: str) -> str:
        if "audit_trail" in query:
            return query
        elif query == "":  # tab completion
            return [x["id"] for x in self.logs]

        try:

            match = self.LogDB.search(self.Q.id == int(query))
            if not match:
                log.warning(f"Unable to gather log id from short index query {query}", show=True)
                typer.echo("Short log_id aliases are built each time 'show logs' is ran.")
                typer.echo("  You can verify the cache by running (hidden command) 'show cache logs'")
                typer.echo("  run 'show logs [OPTIONS]' then use the short index for details")
                raise typer.Exit(1)
            else:
                return match[-1]["long_id"]

        except ValueError as e:
            log.exception(f"Exception in get_log_identifier {e.__class__.__name__}\n{e}")
            typer.secho(f"Exception in get_log_identifier {e.__class__.__name__}", fg="red")
            raise typer.Exit(1)
