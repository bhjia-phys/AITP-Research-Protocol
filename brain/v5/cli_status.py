"""CLI handlers for topic status surfaces."""

from __future__ import annotations

from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.qsgw_cockpit import (
    DEFAULT_QSGW_TOPIC_ID,
    compact_qsgw_cockpit_bundle,
    write_qsgw_cockpit_surfaces,
)
from brain.v5.topic_status import compact_topic_status_bundle, write_topic_status_surfaces
from brain.v5.vnext_readiness import build_vnext_readiness_manifest, compact_vnext_readiness_manifest


def add_status_parser(sp) -> None:
    status = sp.add_parser("status"); ss = status.add_subparsers(dest="status_command", required=True)
    topic = ss.add_parser("topic")
    topic.add_argument("session_id")
    topic.add_argument("--compact", "--progress", action="store_true", dest="compact")
    cockpit = ss.add_parser("qsgw-cockpit")
    cockpit.add_argument("--topic", default=DEFAULT_QSGW_TOPIC_ID, dest="topic_id")
    cockpit.add_argument("--reports-dir", default="")
    cockpit.add_argument("--scripts-dir", default="")
    cockpit.add_argument("--compact", "--progress", action="store_true", dest="compact")
    vnext = ss.add_parser("vnext-readiness")
    vnext.add_argument("--compact", "--progress", action="store_true", dest="compact")


def dispatch_status_command(args, ws) -> dict:
    if args.status_command == "topic":
        bundle = require_valid_public_surface(
            "topic_status_bundle",
            write_topic_status_surfaces(ws, session_id=args.session_id),
        )
        if getattr(args, "compact", False):
            return compact_topic_status_bundle(bundle)
        return bundle
    if args.status_command == "vnext-readiness":
        manifest = require_valid_public_surface("vnext_readiness_manifest", build_vnext_readiness_manifest(ws))
        if getattr(args, "compact", False):
            return compact_vnext_readiness_manifest(manifest)
        return manifest
    if args.status_command == "qsgw-cockpit":
        bundle = require_valid_public_surface(
            "qsgw_cockpit_bundle",
            write_qsgw_cockpit_surfaces(
                ws,
                topic_id=args.topic_id,
                reports_dir=args.reports_dir or None,
                scripts_dir=args.scripts_dir or None,
            ),
        )
        if getattr(args, "compact", False):
            return compact_qsgw_cockpit_bundle(bundle)
        return bundle
    raise SystemExit(f"unsupported status command: {args.status_command}")
