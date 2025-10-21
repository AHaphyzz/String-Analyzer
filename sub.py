word = input("enter a string: ").lower()

# strip and covert word
usage = {
    "text": word
}
print(f"String to analyse: {usage['text']}")

length = len(usage["text"].replace(" ", ""))
print(f"Length: {length}")

word_count = len(usage["text"].split())

print(f"Word count: {word_count}")


unique = []
for char in usage["text"]:
    if usage["text"].count(char) == 1:
        unique.append(char)
unique_characters = len(set(usage["text"]))
print(f"Unique characters: {unique_characters}")

char_fre = {}
for char in usage["text"]:
    if char in char_fre:
        char_fre[char] += 1
    else:
        char_fre[char] = 1
print(char_fre)


cleaned_str = usage["text"].replace(" ", "")
reversed_str = cleaned_str[::-1]
is_palindrome = cleaned_str == reversed_str
print(f"{is_palindrome}, it is a palindrome")


