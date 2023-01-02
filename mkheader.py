#!/usr/bin/env python3

import os
import sys
import argparse
import re

from cmsis_svd.parser import SVDParser
from cmsis_svd.model import SVDRegister, SVDPeripheral, SVDField


class FieldNamespace:
    def __init__(self, fieldObj: SVDField, addr, reg_access=None):
        self.field_comment = "            // %s\n" % (fieldObj.description)
        if reg_access == None:
            self.typedef_decl = "            typedef reg_t<0x%08x, 0x%08x, %d, %s> %s;\n" % (addr, pow(2,fieldObj.bit_width) - 1, fieldObj.bit_offset, self.get_policy(fieldObj.access), fieldObj.name)
        else:
            self.typedef_decl = "            typedef reg_t<0x%08x, 0x%08x, %d, %s> %s;\n" % (addr, pow(2,fieldObj.bit_width) - 1, fieldObj.bit_offset, self.get_policy(reg_access), fieldObj.name)			

    def get_policy(self, access):
        return {
            "read-write" : "rw_t",
            "read-only" : "ro_t",
            "write-only" : "wo_t",
            None : "noacc_t"
        }.get(access, "err")

    def dump(self, fh):
        fh.write(self.field_comment)
        fh.write(self.typedef_decl)


class RegisterNamespace:
    def __init__(self, regObj: SVDRegister, periphBase):
        self.reg_comment = "        // %s\n" % (regObj.description)
        self.reset_const = "            static constexpr uint32_t RESETVALUE = 0x%08x;\n\n" % regObj.reset_value
        self.name = re.sub(r"\W+", "", regObj.name)
        if len(regObj.fields) > 0:
            self.ns_opening = "        namespace "+self.name+"\n        {\n"
            self.ns_close = "        };\n\n"
            self.fields = []
            self.periphBase = periphBase
            if regObj.access != None:
                self.typedef_decl = "            typedef reg_t<0x%08x, 0x%08x, %d, %s> %s;\n" % (periphBase+regObj.address_offset, pow(2,regObj.size) - 1, 0, self.get_policy(regObj.access), regObj.name+"_REG")
            else:
                self.typedef_decl = None
            for field in regObj.fields:
                self.fields.append(FieldNamespace(field, self.periphBase+regObj.address_offset, regObj.access))
        else:
            self.fields = None
            self.typedef_decl = "        typedef reg_t<0x%08x, 0x%08x, %d, %s> %s;\n" % (periphBase+regObj.address_offset, pow(2,regObj.size) - 1, 0, self.get_policy(regObj.access), regObj.name)
    
    def get_policy(self, access):
        return {
            "read-write" : "rw_t",
            "read-only" : "ro_t",
            "write-only" : "wo_t",
            None : "noacc_t"
        }.get(access, "err")

    def dump(self, fh):
        if self.fields != None:
            fh.write(self.reg_comment)
            fh.write(self.ns_opening)
            fh.write(self.reset_const)
            if self.typedef_decl != None:
                fh.write(self.typedef_decl)
            for field in self.fields:
                field.dump(fh)
            fh.write(self.ns_close)
        else:
            fh.write(self.typedef_decl)


class PeripheralNamespace:
    def __init__(self, periphObj: SVDPeripheral):
        self.periph_comment = "    // %s\n" % (periphObj.description)
        self.name = re.sub(r"\W+", "", periphObj.name)
        self.ns_opening = "    namespace "+self.name+"\n    {\n"
        self.ns_close = "    };\n"
        self.regs = []
        for register in periphObj.registers:
            self.regs.append(RegisterNamespace(register, periphObj.base_address))

    def dump(self, fh):
        fh.write(self.periph_comment)
        fh.write(self.ns_opening)
        for reg in self.regs:
            reg.dump(fh)
        fh.write(self.ns_close)


def getProjName(path):
    pathSplit = os.path.split(path)
    return pathSplit[len(pathSplit)-1]


def subst_target(srcfile, dstfile, nameToSub):
    f = open(srcfile, "r")
    f2 = open(dstfile, "w+")
    data = f.read()
    f2.write(data.replace("proj_target", nameToSub))
    f.close()
    f2.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate C++ register header from CMSIS SVD XML file")
    parser.add_argument("input", metavar="inputsvd", nargs=1, help="Input SVD file to generate header from")
    args = parser.parse_args()

    if args.input:
        file = args.input[0]
    else:
        return -1

    parser = SVDParser.for_xml_file(file)
    dev = parser.get_device()
    outfile = f"{dev.name}.hpp"

    with open(outfile, "w") as f:
        f.write("#pragma once\n\n")
        f.write("#include <cstdint>\n")
        f.write("#include \"reg.hpp\"\n")
        f.write("\n\nnamespace %s\n{\n" % dev.name)

        for peripheral in dev.peripherals:
            p = PeripheralNamespace(peripheral)
            p.dump(f)

        f.write("};\n")

    return 0


if __name__ == '__main__':
    sys.exit(main())
