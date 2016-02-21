"""
セクションのパース確認用スクリプト
"""

from argparse import FileType
from itertools import chain, filterfalse
from operator import itemgetter
from pprint import pprint
import sys

from ariblib import caption, packet, sections, table


def parse_pat(args):
    payloads = packet.payloads(packet.packets(args.infile))
    pat = next(table.tables([0x0], [0x0], payloads))
    associations = sections.program_associations(pat)
    for association in associations:
        pprint(association, args.outfile)


def parse_cat(args):
    payloads = packet.payloads(packet.packets(args.infile))
    cat = next(table.tables([0x1], [0x1], payloads))
    accesses = sections.canditional_accesses(cat)
    for access in accesses:
        pprint(access, args.outfile)


def parse_pmt(args):
    payloads = packet.payloads(packet.packets(args.infile))
    pat = next(table.tables([0x0], [0x0], payloads))
    associations = list(sections.program_associations(pat))
    pmt_pids = [association['program_map_pid'] for association
                in sections.program_associations(pat)
                if association['program_number'] != 0]
    pmt = next(table.tables(pmt_pids, [0x2], payloads))
    program_maps = sections.program_maps(pmt)
    for program_map in program_maps:
        pprint(program_map, args.outfile)


def parse_nit(args):
    payloads = packet.payloads(packet.packets(args.infile))
    nit = next(table.tables([0x10], [0x40, 0x41], payloads))
    networks = sections.network_informations(nit)
    for network in networks:
        pprint(network, args.outfile)


def parse_bit(args):
    payloads = packet.payloads(packet.packets(args.infile))
    bit = next(table.tables([0x24], [0xC4], payloads))
    broadcasters = sections.broadcaster_informations(bit)
    for broadcaster in broadcasters:
        pprint(broadcaster, args.outfile)


def parse_sdt(args):
    payloads = packet.payloads(packet.packets(args.infile))
    sdt = table.tables([0x11], [0x42, 0x46], payloads)
    services = chain.from_iterable(map(sections.service_descriptions, sdt))
    for service in services:
        pprint(service, args.outfile)


def parse_tot(args):
    payloads = packet.payloads(packet.packets(args.infile))
    tot = next(table.tables([0x14], [0x73], payloads))
    offset = next(sections.time_offsets(tot))
    pprint(offset, args.outfile)


def parse_cdt(args):
    payloads = packet.payloads(packet.packets(args.infile))
    cdt = table.tables([0x29], [0xC8], payloads)
    data = chain.from_iterable(map(sections.common_data, cdt))
    for datum in data:
        pprint(datum, args.outfile)


def parse_eit(args):
    payloads = packet.payloads(packet.packets(args.infile))
    eit = table.tables([0x12, 0x26, 0x27], list(range(0x4E, 0x70)), payloads)
    events = chain.from_iterable(map(sections.event_informations, eit))
    for event in events:
        pprint(event, args.outfile)


def parse_present_event(args):
    payloads = packet.payloads(packet.packets(args.infile))
    eit = table.tables([0x12], [0x4E], payloads)
    events = chain.from_iterable(map(sections.event_informations, eit))
    present = next(filterfalse(itemgetter('section_number'), events))
    pprint(present, args.outfile)


def parse_next_event(args):
    payloads = packet.payloads(packet.packets(args.infile))
    eit = table.tables([0x12], [0x4E], payloads)
    events = chain.from_iterable(map(sections.event_informations, eit))
    present = next(filter(itemgetter('section_number'), events))
    pprint(present, args.outfile)


def parse_caption(args):
    ts = packet.packets(args.infile)
    payloads = packet.payloads(ts)
    pat = next(table.tables([0x0], [0x0], payloads))
    associations = list(sections.program_associations(pat))
    pmt_pids = [association['program_map_pid'] for association
                in sections.program_associations(pat)
                if association['program_number'] != 0]
    pmt = table.tables(pmt_pids, [0x2], payloads)
    program_maps = chain.from_iterable(map(sections.program_maps, pmt))
    caption_pid = next(
        stream['elementary_pid'] for stream in program_maps
        if stream['stream_type'] == 0x06 and stream['component_tag'] == 0x87)
    args.infile.seek(0)
    base = next(packet.ptses(packet.packets(args.infile)))
    pes = packet.streams(ts, caption_pid)
    captions = chain.from_iterable(map(sections.captions, pes))
    absolutes = caption.absolutize(captions, base, -2)
    srts = caption.srts(absolutes)
    for srt in srts:
        print(srt, file=args.outfile)


def add_parser(parsers):
    parser = parsers.add_parser('section')
    parser.add_argument(
        '--pat', action='store_const', dest='command', const=parse_pat,
        help='parse pat')
    parser.add_argument(
        '--cat', action='store_const', dest='command', const=parse_cat,
        help='parse cat')
    parser.add_argument(
        '--pmt', action='store_const', dest='command', const=parse_pmt,
        help='parse pmt')
    parser.add_argument(
        '--nit', action='store_const', dest='command', const=parse_nit,
        help='parse nit')
    parser.add_argument(
        '--bit', action='store_const', dest='command', const=parse_bit,
        help='parse bit')
    parser.add_argument(
        '--sdt', action='store_const', dest='command', const=parse_sdt,
        help='parse sdt')
    parser.add_argument(
        '--tot', action='store_const', dest='command', const=parse_tot,
        help='parse tot')
    parser.add_argument(
        '--cdt', action='store_const', dest='command', const=parse_cdt,
        help='parse cdt')
    parser.add_argument(
        '--eit', action='store_const', dest='command', const=parse_eit,
        help='parse eit')
    parser.add_argument(
        '--present', action='store_const', dest='command',
        const=parse_present_event,
        help='parse present event')
    parser.add_argument(
        '--next', action='store_const', dest='command',
        const=parse_next_event,
        help='parse next event')
    parser.add_argument(
        '--caption', action='store_const', dest='command',
        const=parse_caption,
        help='parse caption')
    parser.add_argument(
        'infile', nargs='?', type=FileType('rb'), default=sys.stdin)
    parser.add_argument(
        'outfile', nargs='?', type=FileType('w'), default=sys.stdout)