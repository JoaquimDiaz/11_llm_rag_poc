import argparse
import logging
import logging.config
import os
import sys

from rag_poc import config, argument_parsing
from scripts import fetching, indexing

def run(argv: list[str] | None = None) -> None:
    parser = argument_parsing.build_parser()
    args = parser.parse_args(argv)

    config.setup_logging(
        level=argument_parsing.set_verbosity(args.verbose)
        )

    logger = logging.getLogger(__name__)
    logger.debug("verbosity flag count = %s", args.verbose)
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == 'fetch':
        fetching.fetch_data(
            region=args.region,
            limit=args.limit,
            since=args.since,
            until=args.until,
            destination=args.destination
        )
    
    elif args.command == 'index':
        indexing.build_index(
            source=args.source,
            destination=args.destination,
            columns=args.columns,
            id_column=args.id,
        )

    elif args.command == 'app':
        import subprocess
        app_path = os.path.join(os.path.dirname(__file__), "scripts/chat.py")
        subprocess.run(["streamlit", "run", app_path, "--server.port", str(args.port)])

if __name__ == "__main__":
    run(sys.argv[1:])