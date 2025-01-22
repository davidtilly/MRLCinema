import struct
import numpy as np

# parse_msnrbf_2
# Copyright (C) 2022 Adam Johansson
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


def parse_msnrbf_2(srcFile):
    with open(srcFile, 'rb') as fid:
        records = []
        objectIds = []

        nTopLevelRecords = 0
        messageEndRecordFound = False

        while not messageEndRecordFound:
            nTopLevelRecords += 1
            currentTopLevelRecord = parse_Record(fid, records, objectIds)

            if nTopLevelRecords == 1:
                assert currentTopLevelRecord['RecordTypeEnumeration'] == 0, 'SerializationHeaderRecord record MUST be the first record in a binary serialization.'

            if currentTopLevelRecord['RecordTypeName'] == 'MessageEnd':
                messageEndRecordFound = True

        return records

def parse_BinaryArray(fid):
    v = {}
    v['ObjectId'] = struct.unpack('I', fid.read(4))[0]
    v['BinaryArrayTypeEnum'] = struct.unpack('B', fid.read(1))[0]
    v['Rank'] = struct.unpack('i', fid.read(4))[0]
    v['Lengths'] = struct.unpack('i' * v['Rank'], fid.read(4 * v['Rank']))
    if v['BinaryArrayTypeEnum'] in [3, 4, 5]:
        v['LowerBounds'] = struct.unpack('i' * v['Rank'], fid.read(4 * v['Rank']))
    v['TypeEnum'] = struct.unpack('B', fid.read(1))[0]
    v['AdditionalTypeInfo'] = parse_AdditionalInfo(fid, v['TypeEnum'])

    if v['AdditionalTypeInfo']['BinaryTypeName'] in ['Class', 'SystemClass']:
        v['Value'] = parse_multiple_Records(fid, np.prod(v['Lengths']))
    else:
        raise ValueError('Error.')

    return v

def parse_multiple_Records(fid, nRecordsToParse):
    v = [None] * nRecordsToParse
    nParsedRecords = 0
    while nParsedRecords < nRecordsToParse:
        r = parse_Record(fid)
        if r['RecordTypeName'] == 'ObjectNullMultiple256':
            for _ in range(r['RecordValue']['NullCount']):
                nParsedRecords += 1
                v[nParsedRecords - 1] = {'RecordTypeEnumeration': 10, 'RecordTypeName': 'ObjectNull', 'RecordValue': None, 'ObjectId': None}
        else:
            nParsedRecords += 1
            v[nParsedRecords - 1] = r
    return v

def parse_Record(fid, records=None, objectIds=None):
    recordTypeEnumeration = struct.unpack('B', fid.read(1))[0]

    if recordTypeEnumeration == 0:
        recordTypeName = 'SerializationHeaderRecord'
        recordValue = parse_SerializationHeaderRecord(fid)
        objectId = 0
    elif recordTypeEnumeration == 12:
        recordTypeName = 'BinaryLibrary'
        recordValue = parse_BinaryLibrary(fid)
        objectId = recordValue['LibraryId']
    elif recordTypeEnumeration == 5:
        recordTypeName = 'ClassWithMembersAndTypes'
        recordValue = parse_ClassWithMembersAndTypes(fid)
        objectId = recordValue['ClassInfo']['ObjectId']
    elif recordTypeEnumeration == 7:
        recordTypeName = 'BinaryArray'
        recordValue = parse_BinaryArray(fid)
        objectId = recordValue['ObjectId']
    elif recordTypeEnumeration == 9:
        recordTypeName = 'MemberReference'
        recordValue = parse_MemberReference(fid)
        objectId = 0
    elif recordTypeEnumeration == 10:
        recordTypeName = 'ObjectNull'
        recordValue = {}
        objectId = 0
    elif recordTypeEnumeration == 4:
        recordTypeName = 'SystemClassWithMembersAndTypes'
        recordValue = parse_SystemClassWithMembersAndTypes(fid)
        objectId = recordValue['ClassInfo']['ObjectId']
    elif recordTypeEnumeration == 16:
        recordTypeName = 'ArraySingleObject'
        recordValue = parse_ArraySingleObject(fid)
        objectId = recordValue['ArrayInfo']['ObjectId']
    elif recordTypeEnumeration == 13:
        recordTypeName = 'ObjectNullMultiple256'
        recordValue = parse_ObjectNullMultiple256(fid)
        objectId = 0
    elif recordTypeEnumeration == 15:
        recordTypeName = 'ArraySinglePrimitive'
        recordValue = parse_ArraySinglePrimitive(fid)
        objectId = recordValue['ArrayInfo']['ObjectId']
    elif recordTypeEnumeration == 1:
        recordTypeName = 'ClassWithId'
        recordValue = parse_ClassWithId(fid, records)
        objectId = recordValue['ObjectId']
    elif recordTypeEnumeration == 6:
        recordTypeName = 'BinaryObjectString'
        recordValue = parse_BinaryObjectString(fid)
        objectId = recordValue['ObjectId']
    elif recordTypeEnumeration == 11:
        recordTypeName = 'MessageEnd'
        recordValue = {}
        objectId = 0
    else:
        raise ValueError(f'Unknown record type 0x{recordTypeEnumeration:02X} = {recordTypeEnumeration}.')

    r = {'RecordTypeEnumeration': recordTypeEnumeration, 'RecordTypeName': recordTypeName, 'RecordValue': recordValue, 'ObjectId': objectId}

    if records is not None and objectIds is not None:
        records.append(r)
        objectIds.append(objectId)

    return r

def parse_BinaryObjectString(fid):
    v = {}
    v['ObjectId'] = struct.unpack('I', fid.read(4))[0]
    v['Value'] = parse_LengthPrefixedString(fid)
    return v

def parse_ObjectNullMultiple256(fid):
    v = {}
    v['NullCount'] = struct.unpack('B', fid.read(1))[0]
    return v

def parse_ClassWithId(fid, records):
    v = {}
    v['ObjectId'] = struct.unpack('I', fid.read(4))[0]
    v['MetadataId'] = struct.unpack('I', fid.read(4))[0]

    metaDataRecords =[record for record in records if record['ObjectId'] == v['MetadataId']] 
    assert len(metaDataRecords) == 1
    metaDataRecord = metaDataRecords[0]

    v['ClassInfo'] = metaDataRecord['RecordValue']['ClassInfo']
    v['ClassInfo']['ObjectId'] = v['ObjectId']
    v['MemberTypeInfo'] = metaDataRecord['RecordValue']['MemberTypeInfo']

    v['members'] = parse_ClassMembers(fid, v)

    return v

def parse_ArraySinglePrimitive(fid):
    v = {}
    v['ArrayInfo'] = parse_ArrayInfo(fid)
    v['PrimitiveTypeEnum'] = struct.unpack('B', fid.read(1))[0]

    if v['PrimitiveTypeEnum'] == 2:
        v['PrimitiveTypeName'] = 'Byte'
        v['Value'] = struct.unpack(f'{v["ArrayInfo"]["Length"]}B', fid.read(v['ArrayInfo']['Length']))
    else:
        raise ValueError(f'Unknown PrimitiveTypeEnum 0x{v["PrimitiveTypeEnum"]:02X} = {v["PrimitiveTypeEnum"]}.')

    return v

def parse_ArraySingleObject(fid):
    v = {}
    v['ArrayInfo'] = parse_ArrayInfo(fid)
    v['members'] = parse_multiple_Records(fid, v['ArrayInfo']['Length'])
    return v

def parse_ArrayInfo(fid):
    v = {}
    v['ObjectId'] = struct.unpack('I', fid.read(4))[0]
    v['Length'] = struct.unpack('i', fid.read(4))[0]
    return v

def parse_MemberReference(fid):
    v = {}
    v['IdRef'] = struct.unpack('I', fid.read(4))[0]
    return v

def parse_ClassWithMembersAndTypes(fid):
    v = {}
    v['ClassInfo'] = parse_ClassInfo(fid)
    v['MemberTypeInfo'] = parse_MemberTypeInfo(fid, v)
    v['LibraryId'] = struct.unpack('I', fid.read(4))[0]
    v['members'] = parse_ClassMembers(fid, v)
    return v

def parse_ClassMembers(fid, p):
    v = [None] * p['ClassInfo']['MemberCount']

    for iMember in range(p['ClassInfo']['MemberCount']):
        binaryTypeName = p['MemberTypeInfo']['AdditionalInfos'][iMember]['BinaryTypeName']
        if binaryTypeName == 'Class':
            v[iMember] = parse_Record(fid)
            assert v[iMember]['RecordTypeName'] in ['MemberReference', 'ObjectNull', 'ClassWithMembersAndTypes', 'BinaryArray', 'ClassWithId']
        elif binaryTypeName == 'SystemClass':
            v[iMember] = parse_Record(fid)
            assert v[iMember]['RecordTypeName'] in ['MemberReference', 'ObjectNull', 'SystemClassWithMembersAndTypes', 'ArraySingleObject', 'BinaryArray', 'ClassWithId']
        elif binaryTypeName == 'Primitive':
            v[iMember] = parse_Primitive(fid, p['MemberTypeInfo']['AdditionalInfos'][iMember])
        elif binaryTypeName == 'PrimitiveArray':
            v[iMember] = parse_Record(fid)
            assert v[iMember]['RecordTypeName'] == 'MemberReference'
        elif binaryTypeName == 'String':
            v[iMember] = parse_Record(fid)
        else:
            raise ValueError(f'Unknown binary type 0x{p["MemberTypeInfo"]["BinaryTypeEnums"][iMember]:02X} = {p["MemberTypeInfo"]["BinaryTypeEnums"][iMember]} ({binaryTypeName})')

    return v

def parse_Primitive(fid, additionalInfo):
    v = {}
    primitiveTypeEnum = additionalInfo['PrimitiveTypeEnumeration']
    if primitiveTypeEnum == 1:
        v['PrimitiveTypeName'] = 'Boolean'
        v['PrimitiveTypeValue'] = struct.unpack('?', fid.read(1))[0]
    elif primitiveTypeEnum == 6:
        v['PrimitiveTypeName'] = 'Double'
        v['PrimitiveTypeValue'] = struct.unpack('d', fid.read(8))[0]
    elif primitiveTypeEnum == 7:
        v['PrimitiveTypeName'] = 'Int16'
        v['PrimitiveTypeValue'] = struct.unpack('h', fid.read(2))[0]
    elif primitiveTypeEnum == 8:
        v['PrimitiveTypeName'] = 'Int32'
        v['PrimitiveTypeValue'] = struct.unpack('i', fid.read(4))[0]
    elif primitiveTypeEnum == 9:
        v['PrimitiveTypeName'] = 'Int64'
        v['PrimitiveTypeValue'] = struct.unpack('q', fid.read(8))[0]
    elif primitiveTypeEnum == 2:
        v['PrimitiveTypeName'] = 'Byte'
        v['PrimitiveTypeValue'] = struct.unpack('b', fid.read(1))[0]
    elif primitiveTypeEnum == 13:
        v['PrimitiveTypeName'] = 'DateTime'
        v['PrimitiveTypeValue'] = struct.unpack('Q', fid.read(8))[0]
    elif primitiveTypeEnum == 15:
        v['PrimitiveTypeName'] = 'UInt32'
        v['PrimitiveTypeValue'] = struct.unpack('I', fid.read(4))[0]
    else:
        raise ValueError(f'Unknown PrimitiveTypeEnumeration 0x{primitiveTypeEnum:02X} = {primitiveTypeEnum}.')

    return v

def parse_SystemClassWithMembersAndTypes(fid):
    v = {}
    v['ClassInfo'] = parse_ClassInfo(fid)
    v['MemberTypeInfo'] = parse_MemberTypeInfo(fid, v)
    v['members'] = parse_ClassMembers(fid, v)
    return v

def parse_MemberTypeInfo(fid, p):
    v = {}
    v['BinaryTypeEnums'] = struct.unpack(f'{p["ClassInfo"]["MemberCount"]}B', fid.read(p['ClassInfo']['MemberCount']))
    v['AdditionalInfos'] = [None] * p['ClassInfo']['MemberCount']

    for iMember in range(p['ClassInfo']['MemberCount']):
        v['AdditionalInfos'][iMember] = parse_AdditionalInfo(fid, v['BinaryTypeEnums'][iMember])

    return v

def parse_AdditionalInfo(fid, binaryTypeEnum):
    v = {}
    if binaryTypeEnum == 0:
        v['BinaryTypeName'] = 'Primitive'
        v['PrimitiveTypeEnumeration'] = struct.unpack('B', fid.read(1))[0]
    elif binaryTypeEnum == 1:
        v['BinaryTypeName'] = 'String'
    elif binaryTypeEnum == 2:
        v['BinaryTypeName'] = 'Object'
    elif binaryTypeEnum == 3:
        v['BinaryTypeName'] = 'SystemClass'
        v['ClassName'] = parse_LengthPrefixedString(fid)
    elif binaryTypeEnum == 4:
        v['BinaryTypeName'] = 'Class'
        v['TypeName'] = parse_LengthPrefixedString(fid)
        v['LibraryId'] = struct.unpack('I', fid.read(4))[0]
    elif binaryTypeEnum == 5:
        v['BinaryTypeName'] = 'ObjectArray'
    elif binaryTypeEnum == 6:
        v['BinaryTypeName'] = 'StringArray'
    elif binaryTypeEnum == 7:
        v['BinaryTypeName'] = 'PrimitiveArray'
        v['PrimitiveTypeEnumeration'] = struct.unpack('B', fid.read(1))[0]
    else:
        raise ValueError(f'Unknown binary type 0x{binaryTypeEnum:02X} = {binaryTypeEnum}.')

    return v

def parse_ClassInfo(fid):
    v = {}
    v['ObjectId'] = struct.unpack('I', fid.read(4))[0]
    v['Name'] = parse_LengthPrefixedString(fid)
    v['MemberCount'] = struct.unpack('I', fid.read(4))[0]
    v['MemberNames'] = [parse_LengthPrefixedString(fid) for _ in range(v['MemberCount'])]
    return v

def parse_SerializationHeaderRecord(fid):
    v = {}
    v['RootId'] = struct.unpack('I', fid.read(4))[0]
    v['HeaderId'] = struct.unpack('I', fid.read(4))[0]
    v['MajorVersion'] = struct.unpack('I', fid.read(4))[0]
    v['MinorVersion'] = struct.unpack('I', fid.read(4))[0]
    return v

def parse_BinaryLibrary(fid):
    v = {}
    v['LibraryId'] = struct.unpack('I', fid.read(4))[0]
    v['LibraryName'] = parse_LengthPrefixedString(fid)
    return v

def parse_LengthPrefixedString(fid):
    n = 0
    c = 0
    while True:
        b = struct.unpack('B', fid.read(1))[0]
        if b > 127:
            n += (b - 128) * (2 ** (7 * c))
        else:
            n += b * (2 ** (7 * c))
            break
        c += 1
    s = fid.read(n).decode('utf-8')
    return s