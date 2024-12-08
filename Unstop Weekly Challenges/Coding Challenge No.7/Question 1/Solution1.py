def decode(s):
  stack = []
  current = ''
  current_num = 0
  for char in s:
    if char.isdigit():
      current_num = current_num * 10 + int(char)
    elif char == '[':
      stack.append((current,current_num))
      current=''
      current_num=0
    elif char == ']':
      previous_string,num = stack.pop()
      current = previous_string + current * (2* num)
    else:
      current+=char
  return current

def count_perfect_square(length):
  count = 0
  sum_square = 0
  i = 1
  while (i * i) <= length:
    count += 1
    sum_square += i * i
    i += 1
  return count,sum_square

def main():
  encoded=input().strip()
  decoded=decode(encoded)
  count,Sum_Squares = count_perfect_square(len(decoded))
  print(f"{count} {Sum_Squares}")

if __name__ == "__main__":
    main()