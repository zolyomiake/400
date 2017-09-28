
def compress(width, height, pixels, block_size):
    blocks = create_blocks(width, height, block_size)

    compressed_rects = list()
    used_blocks = set()
    uniform_blocks_big = get_uniform_blocks(blocks, pixels, width)
    while True:
        blocks = [b for b in blocks if b[4] not in used_blocks]
        # uniform_blocks = get_uniform_blocks(blocks, pixels, width)
        uniform_blocks = dict()
        for key in uniform_blocks_big.keys():
            uniform_blocks[key] = [b for b in uniform_blocks_big[key]
                                   if b[4] not in used_blocks]

        blobs = get_blobs(uniform_blocks)
        candidate_rects = list()
        # for blob in blobs:
        #     rct = biggest_rect_in_blob(blob)
        #     if rct[0]:
        #         candidate_rects.append(rct)
        #         block_of_rect = get_blocks_of_rect(rct, blocks)
        #         used_blocks |= set([x[4] for x in block_of_rect])
        #         pass

        if candidate_rects:
            compressed_rects.extend(candidate_rects)
        else:
            break

    blocks = create_blocks(width, height, block_size)
    return convert_rects_to_pixel_rects(compressed_rects, blocks)


def convert_rects_to_pixel_rects(compressed_rects, blocks):
    pixel_rects = list()
    for rct in compressed_rects:
        px = rct[0][0]
        py = rct[0][1]
        rightmost = [b for b in blocks if b[6] == rct[0][6] and b[5] == rct[0][5]+rct[1]-1][0]
        bottom = [b for b in blocks if b[5] == rct[0][5] and b[6] == rct[0][6]+rct[2]-1][0]
        width = rightmost[0] + rightmost[2] - px
        height = bottom[1] + bottom[3] - py
        pixel_rects.append((px, py, width, height))
    return pixel_rects



def get_blocks_of_rect(rect, blocks):
    blocks_of_rect = list()
    for dx in range(0, rect[1]):
        for dy in range(0, rect[2]):
            bx = rect[0][5] + dx
            by = rect[0][6] + dy
            btemp = [b for b in blocks if b[5] == bx and b[6] == by]
            blocks_of_rect.append(btemp[0])
    return blocks_of_rect


def get_blobs(uniform_blocks):
    blobs = list()
    for key in uniform_blocks.keys():
        blocks = uniform_blocks[key]
        while blocks:
            blob = grow_blob(blocks, blocks[0])
            ids = set([x[4] for x in blob])
            blobs.append(blob)
            blocks = [x for x in blocks if x[4] not in ids]
    return blobs


def get_uniform_blocks(blocks, pixels, width):
    uniform_blocks = dict()
    for b in blocks:
        values = get_block_contents(b, pixels, width)
        if len(values) == 1:
            value = next(iter(values))
            if value not in uniform_blocks:
                uniform_blocks[value] = list()
            uniform_blocks[value].append(b)
    return uniform_blocks


def biggest_rect_in_blob(blob):
    max_area = 0
    candidate_block = None
    candidate_width = 0
    candidate_height = 0
    for block in blob:
        down = downward_stretch(block, blob)
        right = rightward_stretch(block, blob)
        for r in range(0, right):
            for d in range(0, down):
                if check_rectangle(block, d, r, blob):
                    if d * r > max_area:
                        max_area = d*r
                        candidate_block = block
                        candidate_width = r
                        candidate_height = d

    return candidate_block, candidate_width, candidate_height


def check_rectangle(start_block, down, right, blob):
    for dx in range(0, right):
        for dy in range(0, down):
            target = start_block[5] + dx,  start_block[6] + dy
            block = [b for b in blob if b[5] == target[0] and b[6] == target[1]]
            if not block:
                return False
    return True


def downward_stretch(block, blob):
    block_x = block[5]
    lowest_y = block[6]
    column = [b for b in blob if b[5] == block_x]
    steps = 1
    while True:
        found = False
        for b in column:
            if b[6] == lowest_y + 1:
                lowest_y += 1
                steps += 1
                found = True
                break
        if not found:
            break
    return steps


def rightward_stretch(block, blob):
    block_y = block[6]
    lowest_x = block[5]
    row = [b for b in blob if b[6] == block_y]
    steps = 1
    while True:
        found = False
        for b in row:
            if b[5] == lowest_x + 1:
                lowest_x += 1
                steps += 1
                found = True
                break
        if not found:
            break
    return steps


def grow_blob(blocks, start_block):
    blob = [start_block]
    ids = set([x[4] for x in blob])
    for block in blocks:
        if block[4] not in ids:
            for blob_item in blob:
                if is_block_neighbor(block, blob_item):
                    blob.append(block)
                    ids.add(block[4])
                    break

    return blob


def is_block_neighbor(block1, block2):
    return block1[0] + block1[2] == block2[0] or block2[0] + block2[2] == block1[0] or \
           block1[1] + block1[3] == block2[1] or block2[1] + block2[3] == block1[1]


def create_blocks(im_width, im_height, block_size):
    blocks = list()
    block_id = 0
    blockx_coord = 0
    for x in range(0, im_width, block_size):
        if x + block_size >= im_width:
            block_width = im_width - x
        else:
            block_width = block_size
        blocky_coord = 0
        for y in range(0, im_height, block_size):
            if y + block_size >= im_height:
                block_height = im_height - y
            else:
                block_height = block_size
            block = (x, y, block_width, block_height, block_id, blockx_coord, blocky_coord)
            blocks.append(block)
            block_id += 1
            blocky_coord += 1

        blockx_coord += 1
    return blocks


def get_block_contents(block, pixel_values, width):
    contents = dict()
    # print("Block: {}".format(block))
    for x in range(block[0], block[0]+block[2]):
        for y in range(block[1], block[1] + block[3]):
            offset = y*width + x
            value = pixel_values[offset]
            if value not in contents:
                contents[value] = 1
            else:
                contents[value] += 1
    return contents
