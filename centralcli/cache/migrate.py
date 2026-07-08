import time

from sqlalchemy.orm import Session

from centralcli import api_clients, config, render
from centralcli.constants import CertTypes
from centralcli.models.sql import (
    MPSK,
    CacheTable,
    CentralAuditLog,
    Cert,
    Client,
    Device,
    Event,
    GLPService,
    Group,
    Guest,
    InventoryDevice,
    Label,
    MPSKNetwork,
    Portal,
    Site,
    Subscription,
    SubscriptionName,
    Template,
)

from .tinydb import Cache
from .sqlite import Cache as NewCache

cache = Cache(config)
engine = NewCache(config).engine
api = api_clients.classic


def populate_db(name: str, items: list[CacheTable], explain: str = None):
    _explain = explain and f" [dim italic]{explain}[/]" or ""
    if not items:
        render.econsole.print(f"  :arrow_double_down:  Skipping [cyan]{name}[/]{_explain} cache.  No entries in current cache.")
        return

    with Session(engine) as session:
        start = time.perf_counter()
        session.add_all(items)
        session.commit()
        end = time.perf_counter() - start
        render.econsole.print(f"  :heavy_plus_sign:  Migrated {len(items)} records found in [cyan]{name}[/]{_explain} cache in {round(end, 2)}")


def populate_dev_db():
    devs = [Device(**d) for d in cache.devices]
    return populate_db("devices", devs, explain="MRT devices")


def populate_inv_db():
    inv_devs = [{k if k != "services" else "subscription": v for k, v in dict(d).items()} for d in cache.inventory]
    for dev in inv_devs:
        if isinstance(dev["subscription"], list):  # need to handle older cache where sub was stored as list (as central returned it).  sqlite doesn't support list object.  Need to convert to str or None
            if len(dev["subscription"]) == 1:
                dev["subscription"] = dev["subscription"][0]
            elif not dev["subscription"]:
                dev["subscription"] = None
            else:
                continue  # There should never be more than 1, if there is just ignore the device it will be picked up on subsequent cache refresh after migration.
    inv_devs = [InventoryDevice(**d) for d in inv_devs]
    return populate_db("inventory", inv_devs, explain="[green]GreenLake[/] inventory")


def populate_site_db():
    sites = [Site(**s) for s in cache.sites]
    return populate_db("sites", sites)


def populate_group_db():
    na_keys = ["aos10", "microbranch"]
    cache_groups = [{k: v if k not in na_keys or v != "NA" else None for k, v in dict(group).items()} for group in cache.groups]
    groups = [Group(**g) for g in cache_groups]
    return populate_db("groups", groups)


def populate_template_db():
    templates = [Template(**t) for t in cache.templates]
    return populate_db("templates", templates)


def populate_label_db():
    labels = [Label(**label) for label in cache.labels]
    return populate_db("labels", labels)


def populate_client_db():
    clients = [Client(**{k if k != "connected_port" else "network_port": v for k, v in c.items()}) for c in cache.clients]
    return populate_db("clients", clients)


# picked up here
def populate_sub_db():
    subs = [Subscription(**sub) for sub in cache.subscriptions]
    return populate_db("subscriptions", subs)


def populate_license_db():
    sub_names = [SubscriptionName(name=license) for license in cache.licenses]
    return populate_db("license", sub_names, explain="Valid subscription names")


def populate_cert_db():
    cache_certs = [{**cert, "type": CertTypes(cert['type'])} for cert in cache.certs]
    certs = [Cert(**cert) for cert in cache_certs]
    return populate_db("certs", certs)


def populate_mpsk_db():
    mpsks = [MPSK(**mpsk) for mpsk in cache.mpsk]
    return populate_db("mpsk", mpsks, explain="named MPSKs")


def populate_mpsk_networks_db():
    mpsk_nets = [MPSKNetwork(**mpsk_net) for mpsk_net in cache.mpsk_networks]
    return populate_db("mpsk_networks", mpsk_nets)


def populate_glp_service_db():
    services = [GLPService(**svc) for svc in cache.services]
    return populate_db("services", services, explain="GLP Service info... i.e. Aruba Central")


def populate_guest_db():
    guests = [Guest(**g) for g in cache.guests]
    return populate_db("guest", guests)


def populate_portal_db():
    portals = [Portal(**p) for p in cache.portals]
    return populate_db("portals", portals)


def populate_audit_db():
    audits = [CentralAuditLog(**audit) for audit in cache.LogDB.all()]
    return populate_db("central_audit_logs", audits)


def populate_log_db():
    events = [Event(**event) for event in cache.EventDB.all()]
    return populate_db("events", events, explain="device event logs")


def migrate_all():
    populate_dev_db()
    populate_inv_db()
    populate_site_db()
    populate_group_db()
    populate_template_db()
    populate_label_db()
    populate_client_db()
    populate_license_db()
    populate_cert_db()
    populate_mpsk_db()
    populate_mpsk_networks_db()
    populate_guest_db()
    populate_portal_db()
    populate_audit_db()
    populate_log_db()
    if config.glp.ok:
        populate_glp_service_db()
        populate_sub_db()