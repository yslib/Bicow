
wide22 = [
    # curvature radius, thickness, index of refraction, aperture diameter
    [35.98738, 1.21638, 1.54, 23.716],
    [11.69718, 9.9957, 1, 17.996],
    [13.08714, 5.12622, 1.772, 12.364],
    [22.63294, 1.76924, 1.617, 9.812],
    [71.05802, 0.8184, 1, 9.152],
    [0,        2.27766,0, 8.756],
    [9.58584,2.43254,1.617,8.184],
    [11.28864,0.11506,1,9.152],
    [166.7765,3.09606,1.713,10.648],
    [7.5911,1.32682,1.805,11.44],
    [16.7662,3.98068,1,12.276],
    [7.70286,1.21638,1.617,13.42],
    [11.97328,10,1,17.996]
]
dgauss50 = [
    [29.475,3.76,1.67,25.2],
    [84.83,0.12,1,25.2],
    [19.275,4.025,1.67,23],
    [40.77,3.275,1.699,23],
    [12.75,5.705,1,18],
    [0,4.5,0,17.1],
    [-14.495,1.18,1.603,17],
    [40.77,6.065,1.658,20],
    [-20.385,0.19,1,20],
    [437.065,3.22,1.717,20],
    [-39.73,5.0,1,20]
]
telephoto=[
    [21.851,0	,1.529,19.0],
    [-34.546,5.008,1.599,17.8],
    [108.705,1.502,1.0,16.6],
    [  0,1.127,0,16.2],
    [-12.852,26.965,1.613,12.6],
    [19.813,1.502,1.603,13.4],
    [-20.378,5.008,1.0,14.8]
]
telephoto250=[
    [54.6275,12.52,1.529,47.5],
    [-86.365,3.755,1.599,44.5],
    [271.7625,2.8175,1,41.5],
    [0,67.4125,0,40.5],
    [-32.13,3.755,1.613,31.5],
    [49.5325,12.52,1.603,33.5],
    [-50.945,0,1,37]
]

lense_data={
    'dgauss50':dgauss50,
    'wide22':wide22,
    'telephoto':telephoto,
    'telephoto250':telephoto250
}