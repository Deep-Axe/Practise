# **Question 1**

Rookie is an aspiring cryptographer who has stumbled upon a mysterious encoded string. To crack the code, she must decode the string and analyze its properties. Specifically, after decoding, she wants to count the number of perfect square integers less than or equal to the length of the decoded string and find their sum.
Encoding Rule: K[encoded_string], where the encoded_string inside the square brackets is repeated exactly 2\*K times. Nested encodings are possible, meaning the encoded_string can itself be encoded in the same format.
Rookie needs your help to decode the string and calculate the desired values.

**_<ins>Input Format</ins>:_**\
The first and only line of input cotains the encoded string which we need to decode.\
**_<ins>Output Format</ins>:_**\
Print two space separated integers representing the count and the sum.

### Sample Testcase #0

**_<ins>Testcase Input</ins>:_**\
2[a]3[b]\
**_<ins>Testcase Output</ins>:_**\
3 14\
**_<ins>Explanation</ins>:_**\
Encoded String: 2[a]3[b]\
After decoding: aaaabbbbbb\
String length: 10\
Count of perfect square less than equal to 10 : 1, 4, 9 that is 3\
Sum of perfect squares: 1 + 4 + 9 = 14\

### Sample Testcase #1

**_<ins>Testcase Input</ins>:_**\
2[ab[3[c]]]\
**_<ins>Testcase Output</ins>:_**\
5 55\
**_<ins>Explanation</ins>:_**\
Encoded String: 2[ab3[c]]\
After decoding: abccccccabccccccabccccccabcccccc\
String length: 32\
Count of perfect square less than equal to 32 : 1, 4, 9, 16 and 25 that is 5\
Sum of perfect squares: 1 + 4 + 9 +16 + 25 = 55\
