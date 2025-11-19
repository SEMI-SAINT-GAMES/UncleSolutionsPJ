def my_rand(length=6):
    import random
    import string
    letters_and_digits = string.ascii_letters + string.digits
    result = ''.join(random.choice(letters_and_digits) for i in range(length)).upper()
    print(result)
    return result