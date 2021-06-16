// %%VARIABLE%% will be replaced with consts by python code

#version 430

#define X %%X%%
#define Y %%Y%%
#define Z %%Z%%
#define W %%W%%
#define H %%H%%

layout(local_size_x=X, local_size_y=Y, local_size_z=Z) in;
layout (std430, binding=0) buffer in_0
{
    vec4 inxs[1];
};

layout (std430, binding=1) buffer out_0
{
    vec4 outxs[1];
};

layout (std430, binding=2) buffer uv_0
{
    vec2 uvs[1];
};

#define win_width 5
#define win_height 5
#define win_wh 25
vec4 window[win_wh] = {
    // should manually initialize this
    vec4(0), vec4(0), vec4(0), vec4(0), vec4(0),
    vec4(0), vec4(0), vec4(0), vec4(0), vec4(0),
    vec4(0), vec4(0), vec4(0), vec4(0), vec4(0),
    vec4(0), vec4(0), vec4(0), vec4(0), vec4(0),
    vec4(0), vec4(0), vec4(0), vec4(0), vec4(0)
};

void main()
{
    // define consts
    const int x = int(gl_LocalInvocationID.x);
    const int y = int(gl_WorkGroupID.x);
    const int frag_i = x + y * W;

    int ignored = 0;
    // read window
    for (int win_x = 0; win_x < win_width; win_x++)
    {
        for (int win_y = 0; win_y < win_height; win_y++)
        {
            int win_i = win_y * win_width + win_x;
            int wox = win_x - win_width / 2;
            int woy = win_y - win_height / 2;
            int src_i = x + wox + (y + woy) * W;
            if (src_i < 0 || src_i > W * H)
            {
                window[win_i] = vec4(0, 0, 0, 0);
                ignored++;
                continue;
            }

            window[win_i] = inxs[src_i];
        }
    }

    // simple bubble sort to find median
    while(true)
    {
        bool is_swapped = false;
        for (int win_ii = win_wh - 1; win_ii > 1; win_ii--)
        {
            vec4 now = window[win_ii];
            if (now.w == 0.0) { continue; }
            if (length(window[win_ii - 1]) > length(now))
            {
                // swap
                window[win_ii] = window[win_ii - 1];
                window[win_ii - 1] = now;
                is_swapped = true;
            }
        }

        if (!is_swapped)
        {
            break;
        }
    }
    int median_i = win_wh / 2 + ignored / 2;
    vec4 median = window[median_i];

    // write to buffer
    outxs[frag_i] = vec4(median.xyz, 1.0);
}