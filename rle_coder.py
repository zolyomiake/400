
from operator import itemgetter
import logging


def test_coder():
    # original = [1,2,3,3,3,4,18,18,2,3,4,4,4,5]
    # original = [1, 2, 3, 3, 3, 4, 18, 18, 2, 3, 4, 4, 4, 5, 44, 44, 45, 46, 46, 46, 49, 49, 49, 45]
    original = [1, 2, 0, 0, 0, 0, 3, 3, 3, 4, 18, 18, 2, 3, 4, 4, 4, 5, 44, 44, 45, 46, 46, 46, 49, 49, 49, 45]
    encoded = rle_encode(original)
    decoded = rle_decode(encoded)
    code_matches(original, decoded)


def code_matches(original, decoded):
    if len(original) != len(decoded):
        logging.error("Gebo at array comparison")
        logging.error("orig: %s ", original)
        logging.error("dec:  %s", decoded)
        return
    for i in range(0, len(decoded)):
        if original[i] != decoded[i]:
            logging.error("Gebo at array comparison")
            logging.error("orig: %s ", original)
            logging.error("dec:  %s", decoded)
            return
    logging.info("hooray")


def rle_encode(memberships):
    last_member = None
    repeats = 1
    rle_str = ''
    # ASCII 48 to 57 are digits -> move them above 230 (add 182)
    for member in memberships:
        if 48 <= member < 58:
            member += 182
        if last_member is None:
            last_member = member
            continue
        # if member == last_member:
        #     repeats += 1
        if member == last_member:
            repeats += 1
        else:
            if repeats < 2:
                rle_str += chr(last_member)
            else:
                rle_str += str(repeats) + chr(last_member)
            repeats = 1
        last_member = member

    if repeats != 0:
        if repeats < 2:
            rle_str += chr(last_member)
        else:
            rle_str += str(repeats) + chr(last_member)

    return rle_str


def rle_decode(encoded):
    number_str = ''
    numbers = list()
    for char in encoded:
        if 48 <= ord(char) < 58:
            number_str += char
        else:
            if ord(char) >= 230:
                char = chr(ord(char) - 182)
            if len(number_str) != 0:
                repeat = int(number_str)
                number_str = ''
                for i in range(0, repeat):
                    numbers.append(ord(char))
            else:
                numbers.append(ord(char))
    return numbers


def rle_encode_as_str(memberships):
    last_member = None
    repeats = 0
    rle_str = ''
    # work_array = memberships[:100]
    rep_dict = dict()
    for member in memberships:
        if not last_member:
            last_member = member
        if member == last_member:
            repeats += 1
        else:
            if repeats < 2:
                rle_str += chr(member)
            else:
                if str(repeats) not in rep_dict:
                    rep_dict[str(repeats)] = 1
                else:
                    rep_dict[str(repeats)] += 1
                rle_str += str(repeats) + chr(member)
            repeats = 0
        last_member = member

    if repeats != 0:
        if repeats < 2:
            rle_str += chr(member)
        else:
            rle_str += str(repeats) + chr(member)

    distinct_saving = 0
    savings = list()
    for key in rep_dict.keys():
        cost = len(key) + 1
        repeats = rep_dict[key]
        saving = len(key) * repeats
        profit = saving - cost
        if profit > 0:
            savings.append((key, profit))
            distinct_saving += profit

    savings.sort(key=itemgetter(1), reverse=True)
    # last number is ASCII 57, we're good to go until 255
    char_coded = 58
    # encoding_table = dict()
    enc_str = rle_str
    for saving in savings:
        # encoding_table[saving[0]] = char_coded
        enc_str = enc_str.replace(saving[0], chr(char_coded))
        char_coded += 1
        if char_coded > 255:
            break

    print("Orig {} - mod {}".format(len(rle_str), len(enc_str)))
    return rle_str


def main():
    test_coder()

if __name__ == "__main__":
    main()
