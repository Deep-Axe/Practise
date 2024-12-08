def if_substring_present(S,T):
  j = 0
  for char in S:
    if j < len(T) and char == T[j]:
      j+=1
  return j == len(T)

def find_substring_day(S,T):
  day = 1
  current = S
  while True:
    if if_substring_present(current,T):
      return day
    
    current = current[::-1]
    current+=S
    day+=1

def main():
  S = input().strip()
  T = input().strip()
  result = find_substring_day(S,T)
  print(f"{result}")

if __name__ == "__main__":
  main()