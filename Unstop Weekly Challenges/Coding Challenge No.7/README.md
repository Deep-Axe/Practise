Question 1
Problem Statement
Rookie is an aspiring cryptographer who has stumbled upon a mysterious encoded string. To crack the code, she must decode the string and analyze its properties. Specifically, after decoding, she wants to count the number of perfect square integers less than or equal to the length of the decoded string and find their sum.
Encoding Rule: K[encoded_string], where the encoded_string inside the square brackets is repeated exactly 2*K times. Nested encodings are possible, meaning the encoded_string can itself be encoded in the same format.
Rookie needs your help to decode the string and calculate the desired values.

Sample Testcase #0

Testcase Input
2[a]3[b]
Testcase Output
3 14
Explanation
Encoded String: 2[a]3[b]
After decoding: aaaabbbbbb
String length: 10
Count of perfect square less than equal to 10 : 1, 4, 9 that is 3
Sum of perfect squares: 1 + 4 + 9 = 14

Sample Testcase #1
Testcase Input
2[ab[3[c]]]
Testcase Output
5 55
Explanation
Encoded String: 2[ab3[c]]
After decoding: abccccccabccccccabccccccabcccccc
String length: 32
Count of perfect square less than equal to 32 : 1, 4, 9, 16 and 25 that is 5
Sum of perfect squares: 1 + 4 + 9 +16 + 25 = 55