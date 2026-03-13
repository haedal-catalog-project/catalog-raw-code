# student_code.py
print("=== 파이썬 웹 콘솔 시작 ===")

# 초보자가 짠 익숙한 코드 형태 그대로!
num1 = input("숫자를 입력하세요 1: ")
num2 = input("숫자를 입력하세요 2: ")

try:
    result = float(num1) + float(num2)
    print(f"\n결과 : {result}")
except ValueError:
    print("\n[오류] 숫자를 정확히 입력해주세요.")
    
print("-" * 30)
