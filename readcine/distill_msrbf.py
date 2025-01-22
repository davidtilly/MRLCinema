
import re

def distill_msnrbf(s):

    def distill_record(r):
        if r['RecordTypeName'] == 'SerializationHeaderRecord':
            return distill_serialization_header_record(r)
        elif r['RecordTypeName'] in ['ClassWithMembersAndTypes', 'SystemClassWithMembersAndTypes', 'ClassWithId']:
            return distill_class(r)
        elif r['RecordTypeName'] == 'MemberReference':
            return distill_member_reference(r)
        elif r['RecordTypeName'] == 'ArraySinglePrimitive':
            return distill_array_single_primitive(r)
        elif r['RecordTypeName'] == 'BinaryObjectString':
            return distill_binary_object_string(r)
        elif r['RecordTypeName'] == 'BinaryArray':
            return distill_binary_array(r)
        elif r['RecordTypeName'] == 'ObjectNull':
            return distill_object_null(r)
        else:
            raise ValueError(f'Unknown RecordTypeName "{r["RecordTypeName"]}".')

    def distill_serialization_header_record(r):
        root_records = [x for x in s if x['ObjectId'] == r['RecordValue']['RootId']] 
        assert len(root_records) == 1
        return distill_record(root_records[0])

    def distill_member_reference(r):
        referenced_records = [x for x in s if x['ObjectId'] == r['RecordValue']['IdRef']] 
        assert len(referenced_records) == 1
        return distill_record(referenced_records[0])

    def distill_binary_array(r):
        if len(r['RecordValue']['Lengths']) == 1:
            z = [None] * r['RecordValue']['Lengths'][0]
        else:
            z = [[None] * l for l in r['RecordValue']['Lengths']]

        if r['RecordValue']['AdditionalTypeInfo']['BinaryTypeName'] in ['Class', 'SystemClass']:
            for i_member in range(len(z)):
                z[i_member] = distill_binary_array_member(r, i_member)
        else:
            raise ValueError(f'Unknown BinaryTypeName "{r["RecordValue"]["AdditionalTypeInfo"]["BinaryTypeName"]}".')

        return z

    def distill_binary_array_member(r, i_member):
        binary_type_name = r['RecordValue']['AdditionalTypeInfo']['BinaryTypeName']
        if binary_type_name == 'Class':
            return distill_record(r['RecordValue']['Value'][i_member])
        elif binary_type_name == 'SystemClass':
            return distill_record(r['RecordValue']['Value'][i_member])
        elif binary_type_name == 'Primitive':
            return distill_primitive(r['RecordValue']['members'][i_member])
        elif binary_type_name == 'PrimitiveArray':
            return distill_record(r['RecordValue']['members'][i_member])
        elif binary_type_name == 'String':
            return distill_record(r['RecordValue']['members'][i_member])
        else:
            raise ValueError(f'Unknown BinaryTypeName "{r["RecordValue"]["MemberTypeInfo"]["AdditionalInfos"][i_member]["BinaryTypeName"]}".')

    def distill_object_null(r):
        assert r['RecordTypeName'] == 'ObjectNull'
        return None

    def distill_array_single_primitive(r):
        return r['RecordValue']['Value']

    def distill_binary_object_string(r):
        return r['RecordValue']['Value']

    def distill_class(r):
        z = {}

        for i_member in range(r['RecordValue']['ClassInfo']['MemberCount']):
            name_struct = re.match(r'<(?P<variableName>.*)>k__BackingField', r['RecordValue']['ClassInfo']['MemberNames'][i_member])
            if not name_struct:
                name_struct = re.match(r'_*(?P<variableName>.*)', r['RecordValue']['ClassInfo']['MemberNames'][i_member])
                variable_name = name_struct.group('variableName')
            else:
                variable_name = name_struct.group('variableName')

            z[variable_name] = distill_class_member(r, i_member)

        return z

    def distill_class_member(r, i_member):
        binary_type_name = r['RecordValue']['MemberTypeInfo']['AdditionalInfos'][i_member]['BinaryTypeName']
        if binary_type_name in ['Class', 'SystemClass', 'PrimitiveArray', 'String']:
            return distill_record(r['RecordValue']['members'][i_member])
        elif binary_type_name == 'Primitive':
            return distill_primitive(r['RecordValue']['members'][i_member])
        else:
            raise ValueError(f'Unknown BinaryTypeName "{binary_type_name}".')

    def distill_primitive(p):
        return p['PrimitiveTypeValue']
    
    object_ids = [x['ObjectId'] for x in s]

    assert s[0]['RecordTypeName'] == 'SerializationHeaderRecord'

    z_top = distill_record(s[0])

    return z_top

