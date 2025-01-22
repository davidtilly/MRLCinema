
function result = is_class_wih_members(record)
%IS_CLASS_WIH_MEMBERS Summary of this function goes here
%   Detailed explanation goes here
result = false;

if record.RecordTypeName == "ClassWithMembersAndTypes"
    result = true;
end

end

