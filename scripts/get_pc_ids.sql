#select 'contactId', 'firstName', 'lastName' union 
select contactId, firstName, lastName from ContactInfo where (roles % 2) = 1
#into outfile '/tmp/analysis/pc-ids.csv' 
#fields terminated by ',' enclosed by '"' lines terminated by '\n';
