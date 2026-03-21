-- uses clean_string macro, no model refs
select {{ clean_string('hello') }} as result
