"""
Serialize DPL with custom headers
and with encoded bytecode length.
We are sure bytecode isnt always zero
since there is always the header present.

This more secure since it uses zlib to
somewhat obfuscate the code. But we dont
really need to hide the code, number one
priority is to serialize not to encrypt,
plus even compiled programs can be
reverse engineered.

Old serialization was with a raw dill.dumps
call, no headers and magic bytes, nothing.
This ensures a little protection against
randomly changing the contents of the file.
"""

from . import info
import dill
import struct
import zlib
import hashlib

dill.settings["recurse"] = True

# magic strings "serializer version" will be increamented per update
# of this file, crude way of detecting version misses
# but it is enough.
# 1.4.8 will be cannonical first version
# for serialization.
magic_string = b"DPL "+str(info.VERSION).encode("utf-8")+\
b" : Do not modify! Volatile data may be corrupted! Serializer Version: 0.1 "
magic_s_size = len(magic_string)

header_len_bytes = 2
len_bytes = 8

class InvalidIR:
    class MagicBytes(Exception): ...
    class Length(Exception): ...
    class Hash(Exception): ...

"""
Compiled DPL Script Spec. (for .cdpl files)
All implementations must follow the format below.

File layout:
[hash in hex (64 bytes)]-[is packed flag (1 byte)]:[header length (2 bytes)]
[header (variadic, 64kb max)][Data (variadic)]
[Data length (8 bytes, enough for 4gigs)]

All integers in the format (header length,
Data length, and future values...) must and always
should be in little endian. But everything in the
data or code can be left as is.

The delimimators "-" and ":" are for
readability when skimming through hexdumps.
It is not mandatory to set this bytes to
a specific value and does not change the hash.
Any implementations may skip them without any
problems.

The ".cdpl" file may carry any bytes, not
just pickle or dill dumps.
Think of ELF and WPEF but for ".cdpl" files.

All implementations must name their functions
"dpl_serialize" and "dpl_deserialize" to avoid
misunderstandings and for easy switching of
implementations.

Hash will be used for tamper detection,
it is extracted from hashing the IR or data after
its actual serialization (pickle or dill).
Is packed flag is "p" when compressed and "x" of not,
"x" however is not mandatory as we only check if
its "p" or not.
Header will contain a mandatory magic string
and may also optionally contain data.
IR can be data or executable code.
IR length is for a simpler length based tamper check.

For optional meta data
To specify the data use a
[type (1 byte)][length (2 bytes)] tag for blocks of data.
Notice: magic string must always preceed the metadata
Data types:
    0 - A descriptor string.
        This will be used for DPL internals
        and may not be used by thrid parties
        to store meta data.

        Sample: b"tag:value\\0"
        
        Tag and value will be stripped of white space.
        rstrip for tag meaning " tag" wont be stripped
        and lstrip for value meaning "value " wont be stripped.
        Allows for b"tag : value\\0" formatting.

    1 - A descriptor string for public use.
        Just like above however can be used
        by third party programs.
        This is to avoid clashes with DPL
        internals and for a little bit more freedom.

    2 - Version tag.
        Followed by a 16 bit value.
        May optionally be used.
        Magic string already determines version.

    Types 3 to 127 will be reserved for internals and
    specifically for DPL only.
    
    All types after 127 will be ignored by DPL.
    As the following types are intended for
    debugging or meta data processing.
    
    128 - Vendor tag.
        Followed by a byte (little endian)
        that stores the length of the following
        string (ascii) specifying the vendor tag.
        This can be used to avoid clashing with
        the other data types for other vendors.
        Multiple tags may be used at once, meaning
        all vendors must have compatible types,
        IE vendor one cannot use the types
        unique to vendor two to avoid clashes.
    
    Types 129 and onwards will be free for
    third party programs.

Any new info will be added here.
Even if an external version of this spec exists,
this will be updated for future development.
"""

# we dont name em dpl_*
# since this is the core implementation anyway.
# plus its mine.
def serialize(ir, meta_data=None):
    assert not meta_data, "UNIMPLEMENTED: PROCESS META_DATA"
    packed = False
    ir_encoded = dill.dumps(ir, byref=False)
    if "no-zlib" not in info.program_flags:
        print("Compressing...")
        ir_encoded = zlib.compress(ir_encoded, level=9)
        packed = True
    print("Constructing header data...")
    header = struct.pack(f"{magic_s_size}s", magic_string)
    header_len = len(header)
    header_len_encoded = header_len.to_bytes(header_len_bytes, "little")
    print("Constructing byte array...")
    data = header_len_encoded + header + ir_encoded + len(ir_encoded).to_bytes(len_bytes, "little")
    data = hashlib.sha256(data).hexdigest()\
    .encode("utf-8") + b"-" + ("p" if packed else "x").encode("utf-8") + b":" + data
    return data

def deserialize(data, expected_hash=None):
    """
    If expected_hash is None it is ignored.
    If a sha256 hex hash is given,
    it will compare the extracted hash too.
    
    IE:
      encoded_hash == recomputed_hash
      if expected_hash:
          expected_hash == encoded_hash
          and
          expected_hash == recomputed_hash
    """
    decoded_hash = data[:64].decode("utf-8")
    is_encoded = data[66] == b"p"
    data = data[67:]
    header_len = int.from_bytes(data[:2], "little")
    header = data[header_len_bytes:header_len_bytes+header_len]
    magic_s, = struct.unpack(f"{magic_s_size}s", header[:magic_s_size])
    if magic_s != magic_string:
        raise InvalidIR.MagicBytes("Got unusual magic bytes!\nCauses:\n* Invalid file\n* Corrupted file\n* Version mismatch")
    # TODO: add mechanisms for processing header data.
    header_data = header[magic_s_size:]
    ir_length = int.from_bytes(data[-len_bytes:], "little")
    ir_encoded = data[header_len_bytes+header_len:-len_bytes]
    if "no-zlib" not in info.program_flags:
        ir = dill.loads(zlib.decompress(ir_encoded))
    else:
        ir = dill.loads(ir_encoded)
    if len(ir_encoded) != ir_length:
        raise InvalidIR.Length("IR wasnt the expected length! Try recompilling from source.")
    if decoded_hash != (recomputed_hash:=hashlib.sha256(ir_encoded).hexdigest()):
        raise InvalidIR.Hash("Hash didnt match! Tampered payload?")
    if expected_hash is not None and not (decoded_hash == expected_hash and expected_hash == recomputed_hash):
        raise InvalidIR.Hash("Hash didnt match! Tampered payload?")
    return ir