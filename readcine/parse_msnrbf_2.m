% parse_msnrbf_2 
% Copyright (C) 2022 Adam Johansson
% 
% This program is free software; you can redistribute it and/or
% modify it under the terms of the GNU General Public License
% as published by the Free Software Foundation; either version 2
% of the License, or (at your option) any later version.
% 
% This program is distributed in the hope that it will be useful,
% but WITHOUT ANY WARRANTY; without even the implied warranty of
% MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
% GNU General Public License for more details.
% 
% You should have received a copy of the GNU General Public License
% along with this program; if not, write to the Free Software
% Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

function records = parse_msnrbf_2(srcFile)

fid = fopen(srcFile, 'r', 'l', 'UTF-8');

cleanupObj = onCleanup(@()fclose(fid));

records = [];
objectIds = uint32(zeros(0,1));

nTopLevelRecords = 0;
nRecords = 0;

messageEndRecordFound = false;

while ~messageEndRecordFound
    
    nTopLevelRecords = nTopLevelRecords + 1;
    
    currentTopLevelRecord = parse_Record(fid);
    
    if nTopLevelRecords == 1
        assert(currentTopLevelRecord.RecordTypeEnumeration == 0, 'SerializationHeaderRecord record MUST be the first record in a binary serialization.');
    end
    
    if strcmp(currentTopLevelRecord.RecordTypeName,'MessageEnd')
         messageEndRecordFound = true;
    end

    disp('nRecords')
    disp(nRecords)
    disp(numel(records))
    disp('\n')

end

    function v = parse_BinaryArray(fid)
        
        v.ObjectId = fread(fid, 1, 'uint32=>uint32');
        v.BinaryArrayTypeEnum = fread(fid, 1, 'uint8');
        v.Rank = fread(fid, 1, 'int32');
        v.Lengths = fread(fid, v.Rank, 'int32');
        switch v.BinaryArrayTypeEnum
            case [3 4 5]            
                v.LowerBounds = fread(fid, v.Rank, 'int32');
        end
        v.TypeEnum = fread(fid, 1, 'uint8');
        v.AdditionalTypeInfo = parse_AdditionalInfo(fid, v.TypeEnum);
                
        switch v.AdditionalTypeInfo.BinaryTypeName
            case {'Class','SystemClass'}
                v.Value = parse_multiple_Records(fid, prod(v.Lengths));
            otherwise
                error('Error.');
        end
                
    end

    function v = parse_multiple_Records(fid, nRecordsToParse)
        v = cell(nRecordsToParse, 1);
        nParsedRecords = 0;
        while nParsedRecords < nRecordsToParse
            r = parse_Record(fid);
            if strcmp(r.RecordTypeName,'ObjectNullMultiple256')
                for iNullRecord = 1:r.RecordValue.NullCount
                    nParsedRecords = nParsedRecords + 1;
                    v{nParsedRecords} = struct('RecordTypeEnumeration',uint8(10),'RecordTypeName','ObjectNull','RecordValue',[],'ObjectId',NaN); 
                end
            else
                nParsedRecords = nParsedRecords + 1;
                v{nParsedRecords} = r;
            end
        end
    end

    function r = parse_Record(fid)
        
        recordTypeEnumeration = fread(fid, 1, 'uint8=>uint8');
        
        switch(recordTypeEnumeration)
            case 0
                recordTypeName = 'SerializationHeaderRecord';
                recordValue = parse_SerializationHeaderRecord(fid);
                objectId = uint32(0);
            case 12
                recordTypeName = 'BinaryLibrary';
                recordValue = parse_BinaryLibrary(fid);
                objectId = recordValue.LibraryId;
            case 5
                recordTypeName = 'ClassWithMembersAndTypes';
                recordValue = parse_ClassWithMembersAndTypes(fid);
                objectId = recordValue.ClassInfo.ObjectId;
            case 7
                recordTypeName = 'BinaryArray';
                recordValue = parse_BinaryArray(fid);
                objectId = recordValue.ObjectId;
            case 9
                recordTypeName = 'MemberReference';
                recordValue = parse_MemberReference(fid);
                objectId = uint32(0);
            case 10
                recordTypeName = 'ObjectNull';
                recordValue = struct();
                objectId = uint32(0);
            case 4
                recordTypeName = 'SystemClassWithMembersAndTypes';
                recordValue = parse_SystemClassWithMembersAndTypes(fid);
                objectId = recordValue.ClassInfo.ObjectId;
            case 16
                recordTypeName = 'ArraySingleObject';
                recordValue = parse_ArraySingleObject(fid);     
                objectId = recordValue.ArrayInfo.ObjectId;
            case 13
                recordTypeName = 'ObjectNullMultiple256';
                recordValue = parse_ObjectNullMultiple256(fid);
                objectId = uint32(0);
            case 15
                recordTypeName = 'ArraySinglePrimitive';
                recordValue = parse_ArraySinglePrimitive(fid);
                objectId = recordValue.ArrayInfo.ObjectId;
            case 1
                recordTypeName = 'ClassWithId';
                recordValue = parse_ClassWithId(fid);
                objectId = recordValue.ObjectId;
            case hex2dec('06')
                recordTypeName = 'BinaryObjectString';
                recordValue = parse_BinaryObjectString(fid);
                objectId = recordValue.ObjectId;
            case hex2dec('0B')
                recordTypeName = 'MessageEnd';
                recordValue = struct();
                objectId = uint32(0);
            otherwise
                error('Unknown record type 0x%02X = %.0f.', recordTypeEnumeration, recordTypeEnumeration);
        end
        
        r = struct('RecordTypeEnumeration', recordTypeEnumeration, 'RecordTypeName', recordTypeName, 'RecordValue', recordValue, 'ObjectId', objectId);
        
        nRecords = nRecords + 1;
        if isempty(records)
            records = r;
        else
           records(end+1) = r;
        end
        objectIds(nRecords, 1) = objectId;
        
    end

    function v = parse_BinaryObjectString(fid)
        
        v.ObjectId = fread(fid, 1, 'uint32=>uint32');
        v.Value = parse_LengthPrefixedString(fid);
        
    end

    function v = parse_ObjectNullMultiple256(fid)
        v.NullCount = fread(fid, 1, 'uint8=>uint8');
    end

    function v = parse_ClassWithId(fid)
        
        v.ObjectId = fread(fid, 1, 'uint32=>uint32');
        v.MetadataId = fread(fid, 1, 'uint32=>uint32');
        
        metaDataRecord = records(objectIds ==  v.MetadataId);
        disp(v.MetadataId)
        disp(v.ObjectId)
        disp('\n')
        assert(numel(metaDataRecord) == 1);
        
        v.ClassInfo = metaDataRecord.RecordValue.ClassInfo;
        v.ClassInfo.ObjectId = v.ObjectId;
        v.MemberTypeInfo = metaDataRecord.RecordValue.MemberTypeInfo;
        
        v.members = parse_ClassMembers(fid, v);
        
    end

    function v = parse_ArraySinglePrimitive(fid)
        
        v.ArrayInfo = parse_ArrayInfo(fid);
        v.PrimitiveTypeEnum = fread(fid,1,'uint8=>uint8');
        
        switch v.PrimitiveTypeEnum
            case 2
                v.PrimitiveTypeName = 'Byte';
                v.Value = fread(fid, v.ArrayInfo.Length, 'uint8=>uint8');
            otherwise
                error('Unknown PrimitiveTypeEnum 0x%02X = %.0f.', v.PrimitiveTypeEnum, v.PrimitiveTypeEnum);
        end
        
    end

    function v = parse_ArraySingleObject(fid)
        
        v.ArrayInfo = parse_ArrayInfo(fid);
        
        v.members = parse_multiple_Records(fid, v.ArrayInfo.Length);
        
    end

    function v = parse_ArrayInfo(fid)
        
        v.ObjectId = fread(fid, 1, 'uint32=>uint32');
        v.Length = fread(fid, 1, 'int32=>int32');
        
    end

    function v = parse_MemberReference(fid)
        
        v.IdRef = fread(fid, 1, 'uint32');
        
    end

    function v = parse_ClassWithMembersAndTypes(fid)
        
        v.ClassInfo = parse_ClassInfo(fid);
        disp(v.ClassInfo.Name)
        v.MemberTypeInfo = parse_MemberTypeInfo(fid, v);
        v.LibraryId = fread(fid, 1, 'uint32');
        v.members = parse_ClassMembers(fid, v);
        
    end

    function v = parse_ClassMembers(fid, p)
        
        v = cell(p.ClassInfo.MemberCount,1);
        
        for iMember = 1:p.ClassInfo.MemberCount
            
            switch p.MemberTypeInfo.AdditionalInfos{iMember}.BinaryTypeName
                case 'Class'
                    v{iMember} = parse_Record(fid);
                    assert(ismember(v{iMember}.RecordTypeName, {'MemberReference', 'ObjectNull', 'ClassWithMembersAndTypes', 'BinaryArray', 'ClassWithId'}));
                case 'SystemClass'
                    v{iMember} = parse_Record(fid);
                    assert(ismember(v{iMember}.RecordTypeName, {'MemberReference', 'ObjectNull', 'SystemClassWithMembersAndTypes', 'ArraySingleObject', 'BinaryArray', 'ClassWithId'}));
                case 'Primitive'
                    v{iMember} = parse_Primitive(fid, p.MemberTypeInfo.AdditionalInfos{iMember});
                case 'PrimitiveArray'
                    v{iMember} = parse_Record(fid);
                    assert(ismember(v{iMember}.RecordTypeName, {'MemberReference'}));
                case 'String'
                    v{iMember} = parse_Record(fid);
                otherwise
                    error('Unknown binary type 0x%02X = %.0f (%s)', p.MemberTypeInfo.BinaryTypeEnums(iMember), p.MemberTypeInfo.BinaryTypeEnums(iMember), p.MemberTypeInfo.AdditionalInfos{iMember}.BinaryTypeName);
            end
            
        end
        
    end

    function v = parse_Primitive(fid, additionalInfo)
        
        switch additionalInfo.PrimitiveTypeEnumeration
            case 1
                v.PrimitiveTypeName = 'Boolean';
                v.PrimitiveTypeValue = fread(fid, 1, 'uint8=>logical');
            case 6
                v.PrimitiveTypeName = 'Double';
                v.PrimitiveTypeValue = fread(fid, 1, 'double=>double');
            case 7
                v.PrimitiveTypeName = 'Int16';
                v.PrimitiveTypeValue = fread(fid, 1, 'int16=>int16');
            case 8
                v.PrimitiveTypeName = 'Int32';
                v.PrimitiveTypeValue = fread(fid, 1, 'int32=>int32');
            case 9
                v.PrimitiveTypeName = 'Int64';
                v.PrimitiveTypeValue = fread(fid, 1, 'int64=>int64');
            case 2
                v.PrimitiveTypeName = 'Byte';
                v.PrimitiveTypeValue = fread(fid, 1, 'int8=>int8');
            case 13
                v.PrimitiveTypeName = 'DateTime';
                v.PrimitiveTypeValue = fread(fid, 1, 'uint64=>uint64');
            case 15
                v.PrimitiveTypeName = 'UInt32';
                v.PrimitiveTypeValue = fread(fid, 1, 'uint32=>uint32');
            otherwise
                error('Unknown PrimitiveTypeEnumeration 0x%02X = %.0f.', additionalInfo.PrimitiveTypeEnumeration, additionalInfo.PrimitiveTypeEnumeration);
        end
        
    end

    function v = parse_SystemClassWithMembersAndTypes(fid)
        
        v.ClassInfo = parse_ClassInfo(fid);
        v.MemberTypeInfo = parse_MemberTypeInfo(fid, v);
        v.members = parse_ClassMembers(fid, v);
        
    end

    function v = parse_MemberTypeInfo(fid, p)
        
        v.BinaryTypeEnums = fread(fid, p.ClassInfo.MemberCount, 'uint8');
        
        v.AdditionalInfos = cell(p.ClassInfo.MemberCount, 1);
        
        for iMember = 1:p.ClassInfo.MemberCount
            v.AdditionalInfos{iMember} = parse_AdditionalInfo(fid, v.BinaryTypeEnums(iMember));
        end
        
    end

    function v = parse_AdditionalInfo(fid, binaryTypeEnum)
        switch binaryTypeEnum
            case 0
                v.BinaryTypeName = 'Primitive';
                v.PrimitiveTypeEnumeration = fread(fid, 1, 'uint8');
            case 1
                v.BinaryTypeName = 'String';
            case 2
                v.BinaryTypeName = 'Object';
            case 3
                v.BinaryTypeName = 'SystemClass';
                v.ClassName = parse_LengthPrefixedString(fid);
            case 4
                v.BinaryTypeName = 'Class';
                v.TypeName = parse_LengthPrefixedString(fid);
                v.LibraryId = fread(fid, 1, 'uint32');
            case 5
                v.BinaryTypeName = 'ObjectArray';
            case 6
                v.BinaryTypeName = 'StringArray';
            case 7
                v.BinaryTypeName = 'PrimitiveArray';
                v.PrimitiveTypeEnumeration = fread(fid, 1, 'uint8');
            otherwise
                error('Unknown binary type 0x%02X = %.0f.', binaryTypeEnum, binaryTypeEnum);
        end
    end

    function v = parse_ClassInfo(fid)
        
        v.ObjectId = fread(fid, 1, 'uint32=>uint32');
        v.Name = parse_LengthPrefixedString(fid);
        v.MemberCount = fread(fid, 1, 'uint32');
        v.MemberNames = cell(v.MemberCount, 1);
        for iMember = 1:v.MemberCount
            v.MemberNames{iMember} = parse_LengthPrefixedString(fid);
        end
        
    end

    function v = parse_SerializationHeaderRecord(fid)
        
        v.RootId = fread(fid, 1, 'uint32=>uint32');
        v.HeaderId = fread(fid, 1, 'uint32=>uint32');
        v.MajorVersion = fread(fid, 1, 'uint32=>uint32');
        v.MinorVersion = fread(fid, 1, 'uint32=>uint32');
        
    end

    function v = parse_BinaryLibrary(fid)
        
        v.LibraryId = fread(fid, 1, 'uint32=>uint32');
        v.LibraryName = parse_LengthPrefixedString(fid);
        
    end

    function s = parse_LengthPrefixedString(fid)
        continueReading = true;
        n = 0;
        c = 0;
        while continueReading
            b = fread(fid, 1, 'uint8');
            if b > 127
                n = n + (double(b) - 128)*2^(7*c);
            else
                n = n + double(b)*2^(7*c);
                continueReading = false;
            end
            c = c + 1;
        end
        s = fread(fid, [1 n], 'char=>char');
    end

end