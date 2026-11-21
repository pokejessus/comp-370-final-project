"""Minimal pure-Python reader for bzip2/gzip/xz-compressed .rda files holding data.frames.
Usage: python3 -I rda2csv.py <in_dir> <out_dir>


USE LLM TO HELP US WRITE THIS, NEVER CONVERED RDA TO CSV BEFORE
"""
import bz2, gzip, lzma, struct, sys, csv, os

class R:
    def __init__(self, b):
        self.b, self.i, self.refs = b, 0, []
    def int(self):
        v = struct.unpack('>i', self.b[self.i:self.i+4])[0]; self.i += 4; return v
    def dbl(self):
        v = struct.unpack('>d', self.b[self.i:self.i+8])[0]; self.i += 8; return v
    def header(self):
        assert self.b[:2] == b'X\n', self.b[:10]
        self.i = 2
        self.int(); self.int(); self.int()      # version, writer, min reader
        if self.b[4:8] == b'\x00\x00\x00\x03' or True:
            pass
    def read_header3(self, ver):
        if ver == 3:
            n = self.int(); self.i += n         # native encoding
    def item(self):
        flags = self.int()
        t = flags & 0xFF
        has_attr = bool(flags & (1 << 9)); has_tag = bool(flags & (1 << 10))
        is_obj = bool(flags & (1 << 8))
        if t == 254: return None                # NILVALUE
        if t == 242 or t == 253 or t == 251 or t == 250 or t == 249:   # EMPTYENV, GLOBALENV, MISSINGARG, BASENAMESPACE...
            return None
        if t == 255:                            # REFSXP
            idx = flags >> 8
            if idx == 0: idx = self.int()
            return self.refs[idx-1]
        if t == 1:                              # SYMSXP
            s = self.item(); self.refs.append(s); return s
        if t == 9:                              # CHARSXP
            n = self.int()
            if n == -1: return None
            s = self.b[self.i:self.i+n].decode('utf-8', 'replace'); self.i += n; return s
        if t == 2 or t == 6:                    # LISTSXP / LANGSXP
            attr = self.item() if has_attr else None
            tag = self.item() if has_tag else None
            car = self.item()
            cdr = self.item()
            return ('pair', tag, car, cdr)
        if t in (4, 3, 5, 7, 8, 12, 13, 14, 15, 16, 19, 20, 21, 22, 23, 24, 25):
            pass
        if t == 10 or t == 13:                  # LGLSXP / INTSXP
            n = self.int()
            v = struct.unpack('>%di' % n, self.b[self.i:self.i+4*n]); self.i += 4*n
            v = [None if x == -2147483648 else x for x in v]
            obj = v
        elif t == 14:                           # REALSXP
            n = self.int()
            v = list(struct.unpack('>%dd' % n, self.b[self.i:self.i+8*n])); self.i += 8*n
            obj = [None if x != x else x for x in v]
        elif t == 16:                           # STRSXP
            n = self.int(); obj = []
            for _ in range(n):
                f = self.int(); ln = self.int()
                if ln == -1: obj.append(None)
                else:
                    obj.append(self.b[self.i:self.i+ln].decode('utf-8', 'replace')); self.i += ln
        elif t == 19:                           # VECSXP
            n = self.int(); obj = [self.item() for _ in range(n)]
        elif t == 24:                           # RAWSXP
            n = self.int(); obj = self.b[self.i:self.i+n]; self.i += n
        else:
            raise ValueError('unsupported type %d at %d' % (t, self.i))
        attrs = self.item() if has_attr else None
        return ('vec', t, obj, attrs)

def pairs(p):
    out = {}
    while p:
        _, tag, car, cdr = p
        out[tag] = car; p = cdr
    return out

def to_df(v):
    _, t, cols, attrs = v
    a = pairs(attrs)
    names = a['names'][2]
    rn = a.get('row.names')
    data = []
    for c in cols:
        vals = c[2]
        ca = pairs(c[3]) if c[3] else {}
        if 'levels' in ca:                      # factor
            lv = ca['levels'][2]; vals = [None if x is None else lv[x-1] for x in vals]
        data.append(vals)
    return names, data

def load(path):
    raw = open(path, 'rb').read()
    for op in (bz2.decompress, gzip.decompress, lzma.decompress):
        try: raw = op(raw); break
        except Exception: pass
    assert raw[:5] in (b'RDX2\n', b'RDX3\n'), raw[:10]
    ver = 3 if raw[:5] == b'RDX3\n' else 2
    r = R(raw[5:]); r.header(); r.read_header3(ver)
    top = r.item()
    return {k: to_df(v) for k, v in pairs(top).items()}

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else "."
    dst = sys.argv[2] if len(sys.argv) > 2 else "csv"
    os.makedirs(dst, exist_ok=True)
    for f in sorted(os.listdir(src)):
        if not f.endswith('.rda'): continue
        for name, (cols, data) in load(os.path.join(src, f)).items():
            with open(os.path.join(dst, name + '.csv'), 'w', newline='', encoding='utf-8') as fh:
                w = csv.writer(fh); w.writerow(cols)
                for row in zip(*data): w.writerow(['' if x is None else x for x in row])
            print(name, len(data[0]), 'rows', cols)
