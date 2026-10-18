from textnorm import normalize
a = normalize("Here is the revised passage:\n\nFurther, FIG. 3 shows a device.\n\nNote: I kept the numerals.")
assert a == "Further, FIG. 3 shows a device.", a
b = normalize("DETAILED DESCRIPTION OF THE PREFERRED EMBODIMENTS\n\n[0001] The device100installed here. **Bold** text.")
assert b == "The device 100 installed here. Bold text.", b
c = normalize("TECHNICAL FIELD \n\nThis disclosure relates to X; FIG. 2 is a view.")
assert c == "This disclosure relates to X; FIG. 2 is a view.", c
d = normalize("The sensor comprises a housing.")
assert d == "The sensor comprises a housing."
print("OK")
