from typing import Dict, List, Any, Tuple

import numpy as np

def gpu_pipeline(test_img: Any, size: Tuple[int,int]):
    import moderngl

    W = size[0]
    H = size[1]
    X = W
    Y = 1
    Z = 1
    consts = {
        "W": W,
        "H": H,
        "X": X + 1,
        "Y": Y,
        "Z": Z,
    }

    def source(url, consts):
        ''' read gl code '''
        with open(url, 'r') as fp:
            content = fp.read()

        # feed constant values
        for key, value in consts.items():
            content = content.replace(f"%%{key}%%", str(value))
        return content

    glsl_file = os.path.join(SOURCE_PATH, 'shaders/hdr.glsl')
    context = moderngl.create_standalone_context(require=430)
    compute_shader = context.compute_shader(source(glsl_file, consts))

    # host_low_img = np.random.uniform(0.0, 1.0, (H, W, 4)).astype('f4')
    device_low_img = context.buffer(test_img)

    device_low_img.bind_to_storage_buffer(0)
    # local invocation id x -> pixel x
    # work groupid x -> pixel y
    # eg) buffer[x, y] = gl_LocalInvocationID.x + gl_WorkGroupID.x * W
    compute_shader.run(group_x=H, group_y=1)

    # print out
    output = np.frombuffer(device_low_img.read(), dtype=np.float32)
    output = output.reshape((H, W, 4))
    output = np.multiply(output, 255).astype(np.uint8)