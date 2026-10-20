#!/usr/bin/env python3
import argparse
import pathlib
import re
import struct
import sys
import zlib

SIG = b"Warcraft III recorded game\x1a\x00"
BLOCK_SIZE = 1024 * 1024


def fold_crc16(value: int) -> int:
    return ((value >> 16) ^ (value & 0xFFFF)) & 0xFFFF


def block_checksum(comp_data: bytes, comp_size: int, orig_size: int) -> int:
    header = struct.pack("<III", comp_size, orig_size, 0)
    header_fold = fold_crc16(zlib.crc32(header) & 0xFFFFFFFF)
    data_fold = fold_crc16(zlib.crc32(comp_data) & 0xFFFFFFFF)
    return (data_fold << 16) | header_fold


def parse_header(data: bytes) -> dict:
    if len(data) < 48:
        raise ValueError("file is too small for Warcraft III save header")
    if data[: len(SIG)] != SIG:
        raise ValueError("bad signature")
    header_size, file_size, header_ver, decomp_size, nblocks = struct.unpack_from("<5I", data, len(SIG))
    if header_size < 48 or header_size > len(data):
        raise ValueError(f"bad header_size: {header_size}")
    return {
        "header_size": header_size,
        "file_size": file_size,
        "header_ver": header_ver,
        "decomp_size": decomp_size,
        "nblocks": nblocks,
        "subheader": bytearray(data[48:header_size]),
    }


def write_header_crc(header: bytearray, header_ver: int) -> bytearray:
    crc_off = 64 if header_ver == 1 else 48
    if len(header) >= crc_off + 4:
        header[crc_off : crc_off + 4] = b"\x00\x00\x00\x00"
        crc = zlib.crc32(header) & 0xFFFFFFFF
        struct.pack_into("<I", header, crc_off, crc)
    return header


def iter_blocks(data: bytes, header_size: int, nblocks: int):
    off = header_size
    for index in range(nblocks):
        if off + 12 > len(data):
            raise ValueError(f"block {index}: missing block header")
        comp_size, orig_size, checksum = struct.unpack_from("<III", data, off)
        payload_off = off + 12
        payload_end = payload_off + comp_size
        if payload_end > len(data):
            raise ValueError(f"block {index}: compressed payload extends beyond file")
        yield index, off, comp_size, orig_size, checksum, data[payload_off:payload_end]
        off = payload_end
    if off != len(data):
        raise ValueError(f"trailing bytes after blocks: {len(data) - off}")


def inspect(path: pathlib.Path) -> None:
    data = path.read_bytes()
    meta = parse_header(data)
    print(f"path: {path}")
    print(f"header_size: {meta['header_size']}")
    print(f"file_size_header: {meta['file_size']}")
    print(f"file_size_actual: {len(data)}")
    print(f"header_ver: {meta['header_ver']}")
    print(f"decomp_size_header: {meta['decomp_size']}")
    print(f"nblocks: {meta['nblocks']}")
    total_orig = 0
    for index, off, comp_size, orig_size, checksum, comp_data in iter_blocks(
        data, meta["header_size"], meta["nblocks"]
    ):
        expected = block_checksum(comp_data, comp_size, orig_size)
        status = "OK" if checksum == expected else f"BAD expected={expected:08x}"
        total_orig += orig_size
        print(
            f"block {index}: off={off} comp={comp_size} orig={orig_size} "
            f"checksum={checksum:08x} {status}"
        )
    print(f"decompressed_size_blocks: {total_orig}")


def unpack(save_path: pathlib.Path, raw_path: pathlib.Path) -> None:
    data = save_path.read_bytes()
    meta = parse_header(data)
    raw = bytearray()
    for index, off, comp_size, orig_size, checksum, comp_data in iter_blocks(
        data, meta["header_size"], meta["nblocks"]
    ):
        expected = block_checksum(comp_data, comp_size, orig_size)
        if checksum != expected:
            raise ValueError(
                f"block {index} checksum mismatch at {off}: "
                f"got {checksum:08x}, expected {expected:08x}"
            )
        decompressor = zlib.decompressobj(wbits=15)
        chunk = decompressor.decompress(comp_data)
        if len(chunk) < orig_size:
            raise ValueError(f"block {index} short decompress: got {len(chunk)}, expected {orig_size}")
        raw += chunk[:orig_size]
    raw_path.write_bytes(raw)


def pack(template_path: pathlib.Path, raw_path: pathlib.Path, out_path: pathlib.Path) -> None:
    template = template_path.read_bytes()
    meta = parse_header(template)
    raw = raw_path.read_bytes()

    blocks = []
    for start in range(0, len(raw), BLOCK_SIZE):
        chunk = raw[start : start + BLOCK_SIZE]
        compressor = zlib.compressobj(level=1, wbits=15)
        comp = compressor.compress(chunk) + compressor.flush(zlib.Z_SYNC_FLUSH)
        checksum = block_checksum(comp, len(comp), len(chunk))
        blocks.append((comp, len(chunk), checksum))

    total_size = meta["header_size"] + sum(12 + len(comp) for comp, _, _ in blocks)
    header = bytearray()
    header += SIG
    header += struct.pack(
        "<5I",
        meta["header_size"],
        total_size,
        meta["header_ver"],
        meta["decomp_size"],
        len(blocks),
    )
    header += meta["subheader"]
    out = bytearray(write_header_crc(header, meta["header_ver"]))
    for comp, orig_size, checksum in blocks:
        out += struct.pack("<III", len(comp), orig_size, checksum)
        out += comp
    out_path.write_bytes(out)


def scan_rawcodes(raw_path: pathlib.Path, codes: list[str], context: int) -> None:
    data = raw_path.read_bytes()
    if not codes:
        candidates = sorted(set(re.findall(rb"[A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9]", data)))
        for code in candidates:
            print(code.decode("ascii", errors="replace"))
        return
    for code in codes:
        needle = code.encode("ascii")
        start = 0
        while True:
            pos = data.find(needle, start)
            if pos < 0:
                break
            lo = max(0, pos - context)
            hi = min(len(data), pos + len(needle) + context)
            snippet = data[lo:hi]
            printable = "".join(chr(b) if 32 <= b <= 126 else "." for b in snippet)
            print(f"{code} @ 0x{pos:x}: {printable}")
            start = pos + 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect, unpack, repack, and scan Warcraft III .w3z/.w3v containers.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("inspect")
    p.add_argument("save")

    p = sub.add_parser("unpack")
    p.add_argument("save")
    p.add_argument("raw_output")

    p = sub.add_parser("pack")
    p.add_argument("template")
    p.add_argument("raw")
    p.add_argument("output")

    p = sub.add_parser("scan-rawcodes")
    p.add_argument("raw")
    p.add_argument("codes", nargs="*")
    p.add_argument("--context", type=int, default=32)

    args = parser.parse_args()
    if args.cmd == "inspect":
        inspect(pathlib.Path(args.save))
    elif args.cmd == "unpack":
        unpack(pathlib.Path(args.save), pathlib.Path(args.raw_output))
    elif args.cmd == "pack":
        pack(pathlib.Path(args.template), pathlib.Path(args.raw), pathlib.Path(args.output))
    elif args.cmd == "scan-rawcodes":
        scan_rawcodes(pathlib.Path(args.raw), args.codes, args.context)
    else:
        parser.print_help()
        return 2


if __name__ == "__main__":
    sys.exit(main())
