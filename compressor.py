import sys, struct

def get_char_freqs(data):
  # Parse data to get char frequencies
  char_freqs = {}
  for char in data:
    if char in char_freqs:
      char_freqs[char] += 1
    else:
      char_freqs[char] = 1
  return char_freqs

def get_smallest_element(q1, q2):
  if q2:
    if not q1 or q2[-1][1] < q1[-1][1]:
      return q2.pop(-1)
  if q1:
    if not q2 or q2[-1][1] >= q1[-1][1]:
      return q1.pop(-1)


def build_tree_like_a_sane_person(freqs):
  freqs = [orig + [None, None] for orig in freqs]
  q1, q2 = freqs, []
  while len(q1) + len(q2) > 1:
    first, second = get_smallest_element(q1,q2), get_smallest_element(q1,q2)
    q2.insert(0, [None, first[1] + second[1], first, second])
  return q2

# Encode data using tree
def get_encodings(node, enc, encodings):
  if isinstance(node[2], list):
    get_encodings(node[2], enc + '0', encodings)
  else:
    encodings[node[0]] = enc
  if isinstance(node[3], list):
    get_encodings(node[3], enc + '1', encodings)
  else:
    encodings[node[0]] = enc


# Print human-readable encodings
def print_encodings(encodings):
  for k, v in encodings.iteritems():
    print k,":",v

# Pad bitstrings to length 32
def pad_int_string_to_32(s):
  return '0'*(32 - len(s)) + s

# Main compress function
def compress(input_file, output_file=None):
  if not output_file: output_file = "compressed_"+input_file
  # Read in orig data
  with open(input_file, 'r') as f:
    data = f.read()
  
  char_freqs = get_char_freqs(data)

  # Build list of [char, freq] values sorted by frequency
  freqs = map(list, sorted(char_freqs.iteritems(), key=lambda (k,v):(v,k))[::-1])

  # Build Huffman tree in nested list format
  nested_list_tree = build_tree_like_a_sane_person(freqs)

  # Build dict of char : encoding strings
  encodings = {}
  get_encodings(nested_list_tree[0], '', encodings)  

  # Build bitstring of data from encodings
  encoded = ''
  for char in data:
    encoded += encodings[char]

  # Convert bitstrings into corresponding int values
  to_pack = [int(encoded[i:i+32], 2) for i in range(0, len(encoded)+1, 32)]
  # Store length of bitstring of last data chunk -> could be smaller than 32 bits, and padded with extra zeros
  last_int_string_length = len(bin(to_pack[-1])[2:])
  # Pack encoded data using struct
  packed_data = struct.pack("=%sI" % len(to_pack), *to_pack)
 
  # Write packed data to file
  with open(output_file, 'w') as f:
    # Size of repr of Huffman tree to read the tree
    f.write(str(len(str(nested_list_tree)))+'\n')
    f.write(str(nested_list_tree))
    # Number of chunks/ints packed
    f.write(str(len(to_pack))+'\n')
    # Size of last chunk packed
    f.write(str(last_int_string_length)+'\n')
    f.write(packed_data)


def decode_data(tree, unpacked_string):
  # Decode extracted unpacked data using stored Huffman tree
  decoded = ''
  counter = 0
  while counter < len(unpacked_string)-1:
    node = tree[0]
    while not node[0]:
      # print 'node:',node
      if unpacked_string[counter] == '0':
        node = node[2]
      elif unpacked_string[counter] == '1':
        node = node[3]
      else:
        raise AssertionError("All chars should be 0s or 1s")
      counter += 1 
    decoded += node[0]
  return decoded


def decompress(input_file, output_file=None):
  if not output_file: output_file = 'decompressed_'+input_file

  with open(input_file, 'r') as f:
    # Read compressed data in order of packing
    tree_length = int(f.readline().rstrip())
    tree = eval(f.read(tree_length))
    data_length = int(f.readline().rstrip())
    last_int_string_length = int(f.readline().rstrip())
    packed_data = f.read()

  # Unpack ints from compressed data
  unpacked_ints = struct.unpack("=%sI" % data_length, packed_data)
  # Create list of corresponding binary strings from ints
  unpacked_strings = [pad_int_string_to_32(bin(i)[2:]) for i in unpacked_ints]
  # Concat entire data into one bitstring
  unpacked_string = ''.join(unpacked_strings)
  # Get rid of padded zeros from last data chunk, if any
  unpacked_string = unpacked_string[:-32] + unpacked_string[-last_int_string_length:]

  decoded = decode_data(tree, unpacked_string)

  # Write decompressed data to new file
  with open(output_file, 'w') as f:
    f.write(decoded)


if __name__ == '__main__':
  out = sys.argv[3] if len(sys.argv) > 3 else None
  if sys.argv[1] == 'compress':
    compress(sys.argv[2], out)
  elif sys.argv[1] == 'decompress':
    decompress(sys.argv[2], out)
  else:
    print 'Usage:\n python compressor.py compress input_file [output_file]\n python compressor.py decompress input_file [output_file]'

