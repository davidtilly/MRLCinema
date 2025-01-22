% distill_msnrbf
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

function zTop = distill_msnrbf(s)

objectIds = arrayfun(@(x)x.ObjectId, s);

assert(strcmp(s(1).RecordTypeName,'SerializationHeaderRecord'));

zTop = distill_Record(s(1));

    function z = distill_Record(r)

        switch r.RecordTypeName
            case 'SerializationHeaderRecord'
                z = distill_SerializationHeaderRecord(r);
            case {'ClassWithMembersAndTypes', 'SystemClassWithMembersAndTypes', 'ClassWithId'}
                z = distill_Class(r);
            case 'MemberReference'
                z = distill_MemberReference(r);
            case 'ArraySinglePrimitive'
                z = distill_ArraySinglePrimitive(r);
            case 'BinaryObjectString'
                z = distill_BinaryObjectString(r);
            case 'BinaryArray'
                z = distill_BinaryArray(r);
            case 'ObjectNull'
                z = distill_ObjectNull(r);
            otherwise
                error('Unknown RecordTypeName "%s".', r.RecordTypeName);
        end

    end

    function z = distill_SerializationHeaderRecord(r)

        rootRecord = s(objectIds == r.RecordValue.RootId);
        assert(isscalar(rootRecord));
        z = distill_Record(rootRecord);

    end

    function z = distill_MemberReference(r)

        referencedRecord = s(objectIds == r.RecordValue.IdRef);
        assert(isscalar(referencedRecord));
        z = distill_Record(referencedRecord);

    end

    function z = distill_BinaryArray(r)

        if isscalar(r.RecordValue.Lengths)
            z = cell(r.RecordValue.Lengths, 1);
        else
            z = cell(r.RecordValue.Lengths);
        end

        switch r.RecordValue.AdditionalTypeInfo.BinaryTypeName
            case {'Class', 'SystemClass'}
                for iMember = 1:prod(r.RecordValue.Lengths)
                    z{iMember} = distill_BinaryArrayMember(r, iMember);
                end
            otherwise
                error('Unknown BinaryTypeName "%s".', r.RecordValue.AdditionalTypeInfo.BinaryTypeName);
        end

    end

    function z = distill_BinaryArrayMember(r, iMember)

        switch r.RecordValue.AdditionalTypeInfo.BinaryTypeName
            case {'Class'}
                z = distill_Record(r.RecordValue.Value{iMember});
            case {'SystemClass'}
                z = distill_Record(r.RecordValue.Value{iMember});
            case {'Primitive'}
                z = distill_Primitive(r.RecordValue.members{iMember});
            case {'PrimitiveArray'}
                z = distill_Record(r.RecordValue.members{iMember});
            case {'String'}
                z = distill_Record(r.RecordValue.members{iMember});
            otherwise
                error('Unknown BinaryTypeName "%s".', r.RecordValue.MemberTypeInfo.AdditionalInfos{iMember}.BinaryTypeName);
        end

    end

    function z = distill_ObjectNull(r)
        assert(strcmp(r.RecordTypeName,'ObjectNull'));
        z = [];
    end

    function z = distill_ArraySinglePrimitive(r)

        z = r.RecordValue.Value;

    end

    function z = distill_BinaryObjectString(r)

        z = r.RecordValue.Value;

    end

    function z = distill_Class(r)

        z = struct();

        for iMember = 1:r.RecordValue.ClassInfo.MemberCount

            nameStruct = regexp(r.RecordValue.ClassInfo.MemberNames{iMember},'<(?<variableName>.*)>k__BackingField','names','once');

            if isempty(nameStruct)
                %variableName = genvarname(r.RecordValue.ClassInfo.MemberNames{iMember});
                nameStruct = regexp(r.RecordValue.ClassInfo.MemberNames{iMember},'_*(?<variableName>.*)','names','once');
                variableName = nameStruct.variableName;
            else
                variableName = nameStruct.variableName;
            end

            z.(variableName) = distill_ClassMember(r, iMember);
        end

    end

    function z = distill_ClassMember(r, iMember)

        switch r.RecordValue.MemberTypeInfo.AdditionalInfos{iMember}.BinaryTypeName
            case {'Class', 'SystemClass', 'PrimitiveArray', 'String'}
                z = distill_Record(r.RecordValue.members{iMember});
            case {'Primitive'}
                z = distill_Primitive(r.RecordValue.members{iMember});
            otherwise
                error('Unknown BinaryTypeName "%s".', r.RecordValue.MemberTypeInfo.AdditionalInfos{iMember}.BinaryTypeName);
        end

    end

    function z = distill_Primitive(p)
        z = p.PrimitiveTypeValue;
    end


end
