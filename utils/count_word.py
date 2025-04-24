words = """
</DESIRE_CONFIRMATION> 
<DESIRE> make mojito </DESIRE> 
<META_INTENT> interact with time-dependent tools </META_INTENT> 
<GUIDANCE_TYPE> timer </GUIDANCE_TYPE> 
<CONFIRMATION_CONTENT> Looks like you are going to put lemon into shaker, do you need timer guidance for it? </CONFIRMATION_CONTENT> 
<LOD> low </LOD> 
<TEXT_TITLE> Put lemon into shaker </TEXT_TITLE> 
<TEXT_GUIDANCE_CONTENT> Put lemon into shaker. </TEXT_GUIDANCE_CONTENT> 
<GUIDANCE_FLAG> True </GUIDANCE_FLAG>
    
            """
print(len(words.split()))
print(sum([len(line.split(" ")) for line in words]))
