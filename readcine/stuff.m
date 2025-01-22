
function stuff(records)

for k = 1:numel(records)
    if is_class_with_members(records(k)) 
        if records(k).RecordValue.ClassInfo.ObjectId == 53 
            disp(records(k)); 
        end 
    end
end

end