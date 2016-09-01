import nltk
import codecs
import pprint

pp = pprint.PrettyPrinter(indent=4)
file = codecs.open('docs/1961_program_sri.txt', 'r', "utf-8")

text = file.read()
text = text.replace("\r\n\r\n", "</div><br><div>")
text = "<div>" + text + "</div>"
print(text)

# print(text)