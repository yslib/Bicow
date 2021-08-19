import sys
from numpy.lib.function_base import select
sys.path.append('.')
import taichi as ti
import time
import math
import numpy as np
from renderer_utils import ray_aabb_intersection, intersect_sphere, ray_plane_intersect, reflect, refract

@ti.data_oriented
class Camera:
    def __init__(self, res, camera_pos, fov):
        self.n = 10
        self.fov = ti.field(ti.f32)
        self.camera_pos = ti.Vector.field(3, ti.f32)
        self.aspect_ratio = ti.field(ti.f32)
        self.res = ti.Vector.field(2, ti.i32)
        self.curvatureRadius = ti.field(ti.f32)
        self.thickness = ti.field(ti.f32)
        self.eta = ti.field(ti.f32)
        self.aperture = ti.field(ti.f32)
        self.count_var = ti.field(ti.i32)

        self.lens_z = ti.field(ti.f32)

        ti.root.dense(ti.i, (self.n, )).place(self.curvatureRadius, self.thickness, self.eta, self.aperture)
        ti.root.place(self.res)
        ti.root.place(self.camera_pos)
        ti.root.place(self.aspect_ratio)
        ti.root.place(self.fov)
        ti.root.place(self.count_var)
        ti.root.place(self.lens_z)

        self.aspect_ratio[None] = float(res[0])/res[1]
        self.res = ti.Vector([400, 400])
        self.fov[None] = fov
        self.camera_pos = ti.Vector([*camera_pos])

        self.stratify_res = 5
        self.inv_stratify = 1.0 / 5.0
        self.count_var[None] = 0
        self.loaded = False

    @ti.func
    def gen_ray(self, u:ti.template(), v:ti.template()):
        pos = self.camera_pos
        cur_iter = self.count_var[None]
        str_x, str_y = (cur_iter / self.stratify_res), (cur_iter % self.stratify_res)
        ray_dir = ti.Vector([
            (2 * self.fov[None] * (u + (str_x) * self.inv_stratify) / res[1] -
             self.fov[None] * self.aspect_ratio[None] - 1e-5),
            (2 * self.fov[None] * (v + (str_y) * self.inv_stratify) / res[1] -
             self.fov[None] - 1e-5),
            -1.0,
        ])
        ray_dir = ray_dir.normalized()
        return ray_dir

    @ti.func
    def count_add(self):
        self.count_var[None] = (self.count_var[None] + 1) % (stratify_res * stratify_res)

    @ti.func
    def intersect_with_sphere(self,
                            center:ti.template(),
                            radius: ti.template(),
                            ro:ti.Vector,
                            rd:ti.Vector):
        """
        A specialization for evaluating the intersection of ray and sphere which center is along z-axis
        Returns the ray paramter t and the intersection normal
        """
        t = 0.0
        n = ti.Vector([0.0,0.0,0.0])
        return True, t, n

    @ti.func
    def lensZ(self):
        if self.loaded:
            return self.lens_z[None]
        self.loaded = True
        z = 0.0
        for i in range(10):
            z += self.thickness[i]
        self.lens_z[None] = z
        return z

    @ti.func
    def gen_ray_from_scene(self, ori, dir):
        ro, rd = ti.Vector([ori.x, ori.y, -ori.z]), ti.Vector([dir.x, dir.y, -dir.z])
        elemZ = self.lensZ()

        for i in ti.static(range(10)):
            is_stop = self.curvatureRadius[i] == 0.0
            if is_stop:
                t = (elemZ - ro.z) / rd.z
            else:
                radius = self.curvatureRadius[i]
                centerZ = elemZ + radius
                isect, t, n = self.intersect_with_sphere(centerZ, radius, ro, rd)
                if not isect:
                    return False, ro, rd

            hit = ro + rd * t
            r = hit.x * hit.x + hit.y * hit.y
            if r > self.aperture[i] * self.aperture[i]:  # out of the element aperture
                return False, ro, rd

            if not is_stop:
                # refracted by lens
                etaI = 1.0 if i == 0 or self.eta[i - 1] == 0.0 else self.eta[i - 1]
                etaT = self.eta[i] if self.eta[i] != 0.0 else 1.0
                rd.normalized()
                has_r, d = refract(-rd, n, etaI/etaT)
                if not has_r:
                    return False, ro, rd
                rd = ti.Vector([d.x, d.y, d.z])

            elemZ += self.thickness[i]

        return True, ti.Vector([ro.x, ro.y, -ro.z]), ti.Vector([rd.x, rd.y, rd.z])

    @ti.func
    def gen_ray_from_film(self, ori: ti.Vector, dir:ti.Vector):
        """
        Input ray is the initial ray sampled from film to the rear lens element.
        Returns True and the output ray if the ray could be pass the lens system
        or returns False
        """
        ro, rd = ti.Vector([ori.x, ori.y, -ori.z]), ti.Vector([dir.x, dir.y, -dir.z])
        elemZ = 0.0
        for i in ti.static(range(10 - 1, -1, -1)):
            elemZ -= self.thickness[i]
            is_stop = self.curvatureRadius[i] == 0.0
            if is_stop:
                if rd.z >= 0.0:
                    return False, ro, rd
                t = (elemZ - ro.z) / rd.z
            else:
                radius = self.curvatureRadius[i]
                centerZ = elemZ + radius
                isect, t, n = self.intersect_with_sphere(centerZ, radius, ro, rd)
                if not isect:
                    return False, ro, rd

            hit = ro + rd * t
            r = hit.x * hit.x + hit.y * hit.y
            if r > self.aperture[i] * self.aperture[i]:  # out of the element aperture
                return False, ro, rd

            ro = ti.Vector([hit.x, hit.y, hit.z])

            if not is_stop:
                # refracted by lens
                etaI = self.eta[i]
                etaT = self.eta[i - 1] if i > 0 and self.eta[i - 1] != 0.0 else 1.0   # the outer of 0-th element is air, whose eta is 1.0
                rd.normalized()
                has_r, d = refract(-rd, n, etaI/etaT)
                if not has_r:
                    return False, ro, rd
                rd = ti.Vector([d.x, d.y, d.z])

        return True, ti.Vector([ro.x, ro.y, -ro.z]), ti.Vector([rd.x, rd.y, rd.z])



ti.init(arch=ti.gpu)
res = (400, 400)
color_buffer = ti.Vector.field(3, dtype=ti.f32, shape=res)
count_var = ti.field(ti.i32, shape=(1, ))

max_ray_depth = 10
eps = 1e-4
inf = 1e10
fov = 0.8

camera_pos = ti.Vector([0.0, 0.6, 3.0])

mat_none = 0
mat_lambertian = 1
mat_specular = 2
mat_glass = 3
mat_light = 4

light_y_pos = 2.0 - eps
light_x_min_pos = -0.25
light_x_range = 0.5
light_z_min_pos = 1.0
light_z_range = 0.12
light_area = light_x_range * light_z_range
light_min_pos = ti.Vector([light_x_min_pos, light_y_pos, light_z_min_pos])
light_max_pos = ti.Vector([
    light_x_min_pos + light_x_range, light_y_pos,
    light_z_min_pos + light_z_range
])
light_color = ti.Vector(list(np.array([0.9, 0.85, 0.7])))
light_normal = ti.Vector([0.0, -1.0, 0.0])

# No absorbtion, integrates over a unit hemisphere
lambertian_brdf = 1.0 / math.pi
# diamond!
refr_idx = 2.4

# right near sphere
sp1_center = ti.Vector([0.4, 0.225, 1.75])
sp1_radius = 0.22
# left far sphere
sp2_center = ti.Vector([-0.28, 0.55, 0.8])
sp2_radius = 0.32


cam = Camera((400, 400), (0.0, 0.6, 3.0),0.8)

def make_box_transform_matrices():
    rad = math.pi / 8.0
    c, s = math.cos(rad), math.sin(rad)
    rot = np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]])
    translate = np.array([
        [1, 0, 0, -0.7],
        [0, 1, 0, 0],
        [0, 0, 1, 0.7],
        [0, 0, 0, 1],
    ])
    m = translate @ rot
    m_inv = np.linalg.inv(m)
    m_inv_t = np.transpose(m_inv)
    return ti.Matrix(m_inv), ti.Matrix(m_inv_t)


# left box
box_min = ti.Vector([0.0, 0.0, 0.0])
box_max = ti.Vector([0.55, 1.1, 0.55])
box_m_inv, box_m_inv_t = make_box_transform_matrices()


@ti.func
def intersect_light(pos, d, tmax):
    hit, t, _ = ray_aabb_intersection(light_min_pos, light_max_pos, pos, d)
    if hit and 0 < t < tmax:
        hit = 1
    else:
        hit = 0
        t = inf
    return hit, t


@ti.func
def ray_aabb_intersection2(box_min, box_max, o, d):
    # Compared to ray_aabb_intersection2(), this also returns the normal of
    # the nearest t.
    intersect = 1

    near_t = -inf
    far_t = inf
    near_face = 0
    near_is_max = 0

    for i in ti.static(range(3)):
        if d[i] == 0:
            if o[i] < box_min[i] or o[i] > box_max[i]:
                intersect = 0
        else:
            i1 = (box_min[i] - o[i]) / d[i]
            i2 = (box_max[i] - o[i]) / d[i]

            new_far_t = max(i1, i2)
            new_near_t = min(i1, i2)
            new_near_is_max = i2 < i1

            far_t = min(new_far_t, far_t)
            if new_near_t > near_t:
                near_t = new_near_t
                near_face = int(i)
                near_is_max = new_near_is_max

    near_norm = ti.Vector([0.0, 0.0, 0.0])
    if near_t > far_t:
        intersect = 0
    if intersect:
        # TODO: Issue#1004...
        if near_face == 0:
            near_norm[0] = -1 + near_is_max * 2
        elif near_face == 1:
            near_norm[1] = -1 + near_is_max * 2
        else:
            near_norm[2] = -1 + near_is_max * 2

    return intersect, near_t, far_t, near_norm


@ti.func
def mat_mul_point(m, p):
    hp = ti.Vector([p[0], p[1], p[2], 1.0])
    hp = m @ hp
    hp /= hp[3]
    return ti.Vector([hp[0], hp[1], hp[2]])


@ti.func
def mat_mul_vec(m, v):
    hv = ti.Vector([v[0], v[1], v[2], 0.0])
    hv = m @ hv
    return ti.Vector([hv[0], hv[1], hv[2]])


@ti.func
def ray_aabb_intersection2_transformed(box_min, box_max, o, d):
    # Transform the ray to the box's local space
    obj_o = mat_mul_point(box_m_inv, o)
    obj_d = mat_mul_vec(box_m_inv, d)
    intersect, near_t, _, near_norm = ray_aabb_intersection2(
        box_min, box_max, obj_o, obj_d)
    if intersect and 0 < near_t:
        # Transform the normal in the box's local space to world space
        near_norm = mat_mul_vec(box_m_inv_t, near_norm)
    else:
        intersect = 0
    return intersect, near_t, near_norm


@ti.func
def intersect_scene(pos, ray_dir):
    closest, normal = inf, ti.Vector.zero(ti.f32, 3)
    c, mat = ti.Vector.zero(ti.f32, 3), mat_none

    # right near sphere
    cur_dist, hit_pos = intersect_sphere(pos, ray_dir, sp1_center, sp1_radius)
    if 0 < cur_dist < closest:
        closest = cur_dist
        normal = (hit_pos - sp1_center).normalized()
        c, mat = ti.Vector([1.0, 1.0, 1.0]), mat_glass
    # left box
    hit, cur_dist, pnorm = ray_aabb_intersection2_transformed(
        box_min, box_max, pos, ray_dir)
    if hit and 0 < cur_dist < closest:
        closest = cur_dist
        normal = pnorm
        c, mat = ti.Vector([0.8, 0.5, 0.4]), mat_specular

    # left
    pnorm = ti.Vector([1.0, 0.0, 0.0])
    cur_dist, _ = ray_plane_intersect(pos, ray_dir, ti.Vector([-1.1, 0.0,
                                                               0.0]), pnorm)
    if 0 < cur_dist < closest:
        closest = cur_dist
        normal = pnorm
        c, mat = ti.Vector([0.65, 0.05, 0.05]), mat_lambertian
    # right
    pnorm = ti.Vector([-1.0, 0.0, 0.0])
    cur_dist, _ = ray_plane_intersect(pos, ray_dir, ti.Vector([1.1, 0.0, 0.0]),
                                      pnorm)
    if 0 < cur_dist < closest:
        closest = cur_dist
        normal = pnorm
        c, mat = ti.Vector([0.12, 0.45, 0.15]), mat_lambertian
    # bottom
    gray = ti.Vector([0.93, 0.93, 0.93])
    pnorm = ti.Vector([0.0, 1.0, 0.0])
    cur_dist, _ = ray_plane_intersect(pos, ray_dir, ti.Vector([0.0, 0.0, 0.0]),
                                      pnorm)
    if 0 < cur_dist < closest:
        closest = cur_dist
        normal = pnorm
        c, mat = gray, mat_lambertian
    # top
    pnorm = ti.Vector([0.0, -1.0, 0.0])
    cur_dist, _ = ray_plane_intersect(pos, ray_dir, ti.Vector([0.0, 2.0, 0.0]),
                                      pnorm)
    if 0 < cur_dist < closest:
        closest = cur_dist
        normal = pnorm
        c, mat = gray, mat_lambertian
    # far
    pnorm = ti.Vector([0.0, 0.0, 1.0])
    cur_dist, _ = ray_plane_intersect(pos, ray_dir, ti.Vector([0.0, 0.0, 0.0]),
                                      pnorm)
    if 0 < cur_dist < closest:
        closest = cur_dist
        normal = pnorm
        c, mat = gray, mat_lambertian
    # light
    hit_l, cur_dist = intersect_light(pos, ray_dir, closest)
    if hit_l and 0 < cur_dist < closest:
        # technically speaking, no need to check the second term
        closest = cur_dist
        normal = light_normal
        c, mat = light_color, mat_light

    return closest, normal, c, mat


@ti.func
def visible_to_light(pos, ray_dir):
    a, b, c, mat = intersect_scene(pos, ray_dir)
    return mat == mat_light


@ti.func
def dot_or_zero(n, l):
    return max(0.0, n.dot(l))


@ti.func
def mis_power_heuristic(pf, pg):
    # Assume 1 sample for each distribution
    f = pf**2
    g = pg**2
    return f / (f + g)


@ti.func
def compute_area_light_pdf(pos, ray_dir):
    hit_l, t = intersect_light(pos, ray_dir, inf)
    pdf = 0.0
    if hit_l:
        l_cos = light_normal.dot(-ray_dir)
        if l_cos > eps:
            tmp = ray_dir * t
            dist_sqr = tmp.dot(tmp)
            pdf = dist_sqr / (light_area * l_cos)
    return pdf


@ti.func
def compute_brdf_pdf(normal, sample_dir):
    return dot_or_zero(normal, sample_dir) / math.pi


@ti.func
def sample_area_light(hit_pos, pos_normal):
    # sampling inside the light area
    x = ti.random() * light_x_range + light_x_min_pos
    z = ti.random() * light_z_range + light_z_min_pos
    on_light_pos = ti.Vector([x, light_y_pos, z])
    return (on_light_pos - hit_pos).normalized()


@ti.func
def sample_brdf(normal):
    # cosine hemisphere sampling
    # first, uniformly sample on a disk (r, theta)
    r, theta = 0.0, 0.0
    sx = ti.random() * 2.0 - 1.0
    sy = ti.random() * 2.0 - 1.0
    if sx >= -sy:
        if sx > sy:
            # first region
            r = sx
            div = abs(sy / r)
            if sy > 0.0:
                theta = div
            else:
                theta = 7.0 + div
        else:
            # second region
            r = sy
            div = abs(sx / r)
            if sx > 0.0:
                theta = 1.0 + sx / r
            else:
                theta = 2.0 + sx / r
    else:
        if sx <= sy:
            # third region
            r = -sx
            div = abs(sy / r)
            if sy > 0.0:
                theta = 3.0 + div
            else:
                theta = 4.0 + div
        else:
            # fourth region
            r = -sy
            div = abs(sx / r)
            if sx < 0.0:
                theta = 5.0 + div
            else:
                theta = 6.0 + div
    # Malley's method
    u = ti.Vector([1.0, 0.0, 0.0])
    if abs(normal[1]) < 1 - eps:
        u = normal.cross(ti.Vector([0.0, 1.0, 0.0]))
    v = normal.cross(u)

    theta = theta * math.pi * 0.25
    costt, sintt = ti.cos(theta), ti.sin(theta)
    xy = (u * costt + v * sintt) * r
    zlen = ti.sqrt(max(0.0, 1.0 - xy.dot(xy)))
    return xy + zlen * normal


@ti.func
def sample_direct_light(hit_pos, hit_normal, hit_color):
    direct_li = ti.Vector([0.0, 0.0, 0.0])
    fl = lambertian_brdf * hit_color * light_color
    light_pdf, brdf_pdf = 0.0, 0.0
    # sample area light
    to_light_dir = sample_area_light(hit_pos, hit_normal)
    if to_light_dir.dot(hit_normal) > 0:
        light_pdf = compute_area_light_pdf(hit_pos, to_light_dir)
        brdf_pdf = compute_brdf_pdf(hit_normal, to_light_dir)
        if light_pdf > 0 and brdf_pdf > 0:
            l_visible = visible_to_light(hit_pos, to_light_dir)
            if l_visible:
                w = mis_power_heuristic(light_pdf, brdf_pdf)
                nl = dot_or_zero(to_light_dir, hit_normal)
                direct_li += fl * w * nl / light_pdf
    # sample brdf
    brdf_dir = sample_brdf(hit_normal)
    brdf_pdf = compute_brdf_pdf(hit_normal, brdf_dir)
    if brdf_pdf > 0:
        light_pdf = compute_area_light_pdf(hit_pos, brdf_dir)
        if light_pdf > 0:
            l_visible = visible_to_light(hit_pos, brdf_dir)
            if l_visible:
                w = mis_power_heuristic(brdf_pdf, light_pdf)
                nl = dot_or_zero(brdf_dir, hit_normal)
                direct_li += fl * w * nl / brdf_pdf
    return direct_li


@ti.func
def schlick(cos, eta):
    r0 = (1.0 - eta) / (1.0 + eta)
    r0 = r0 * r0
    return r0 + (1 - r0) * ((1.0 - cos)**5)


@ti.func
def sample_ray_dir(indir, normal, hit_pos, mat):
    u = ti.Vector([0.0, 0.0, 0.0])
    pdf = 1.0
    if mat == mat_lambertian:
        u = sample_brdf(normal)
        pdf = max(eps, compute_brdf_pdf(normal, u))
    elif mat == mat_specular:
        u = reflect(indir, normal)
    elif mat == mat_glass:
        cos = indir.dot(normal)
        ni_over_nt = refr_idx
        outn = normal
        if cos > 0.0:
            outn = -normal
            cos = refr_idx * cos
        else:
            ni_over_nt = 1.0 / refr_idx
            cos = -cos
        has_refr, refr_dir = refract(indir, outn, ni_over_nt)
        refl_prob = 1.0
        if has_refr:
            refl_prob = schlick(cos, refr_idx)
        if ti.random() < refl_prob:
            u = reflect(indir, normal)
        else:
            u = refr_dir
    return u.normalized(), pdf


stratify_res = 5
inv_stratify = 1.0 / 5.0


@ti.kernel
def render():
    for u, v in color_buffer:
        ray_dir = cam.gen_ray(u, v)
        acc_color = ti.Vector([0.0, 0.0, 0.0])
        throughput = ti.Vector([1.0, 1.0, 1.0])
        depth = 0
        while depth < max_ray_depth:
            closest, hit_normal, hit_color, mat = intersect_scene(pos, ray_dir)
            if mat == mat_none:
                break

            hit_pos = pos + closest * ray_dir
            hit_light = (mat == mat_light)
            if hit_light:
                acc_color += throughput * light_color
                break
            elif mat == mat_lambertian:
                acc_color += throughput * sample_direct_light(
                    hit_pos, hit_normal, hit_color)

            depth += 1
            ray_dir, pdf = sample_ray_dir(ray_dir, hit_normal, hit_pos, mat)
            pos = hit_pos + 1e-4 * ray_dir
            if mat == mat_lambertian:
                throughput *= lambertian_brdf * hit_color * dot_or_zero(
                    hit_normal, ray_dir) / pdf
            else:
                throughput *= hit_color
        color_buffer[u, v] += acc_color
    count_var[0] = (count_var[0] + 1) % (stratify_res * stratify_res)
    cam.count_add()


gui = ti.GUI('Realistic camera', res)
last_t = time.time()
i = 0
while gui.running:
    render()
    interval = 10
    if i % interval == 0 and i > 0:
        img = color_buffer.to_numpy() * (1 / (i + 1))
        img = np.sqrt(img / img.mean() * 0.24)
        print("{:.2f} samples/s ({} iters, var={})".format(
            interval / (time.time() - last_t), i, np.var(img)))
        last_t = time.time()
        gui.set_image(img)
        gui.show()
    i += 1
