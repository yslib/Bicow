import taichi as ti
from demo import lens, renderer_utils
from renderer_utils import refract, intersect_sphere

elements_count = 10
pupil_interval_count = 64
eps = 1e-5


@ti.func
def lerp(val, begin ,end):
    return begin * (1.0 - val) + val * end

@ti.func
def bound_union_with(bmin, bmax, pos):
    return ti.min(bmin, pos), ti.max(bmax, pos)

@ti.func
def make_bound2():
    return ti.Vector([99999.0, 99999.0]), ti.Vector([-99999.0,-99999.0])

@ti.func
def inside_aabb(bmin, bmax, pos):
    return all(bmin <= pos) and all(pos <= bmax)

@ti.func
def radical_inverse_2(value):
    return 1.0

@ti.func
def radical_inverse_3(value):
    inv_base = 1.0/3.0
    reversed = 0
    n = 1.0
    while value != 0:
        next = value / 3
        _digit = value - next * 3
        reversed = reversed * 3 + _digit
        n *= inv_base
        value = next
    return reversed * n


@ti.data_oriented
class RealisticCamera:
    def __init__(self, res, camera_pos):
        self.camera_pos = ti.Vector.field(3, ti.f32)
        self.aspect_ratio = ti.field(ti.f32)
        self.res = ti.Vector.field(2, ti.i32)
        self.curvatureRadius = ti.field(ti.f32)
        self.thickness = ti.field(ti.f32)
        self.eta = ti.field(ti.f32)
        self.aperture = ti.field(ti.f32)
        self.exitPupilBoundMin = ti.Vector.field(ti.f32)
        self.exitPupilBoundMax = ti.Vector.field(ti.f32)
        self.film_diagnal = 35.00

        self.lens_z = ti.field(ti.f32)

        ti.root.dense(ti.i, (elements_count, )).place(self.curvatureRadius, self.thickness, self.eta, self.aperture)
        ti.root.dense(ti.i, (pupil_interval_count, )).place(self.exitPupilBoundMin, self.exitPupilBoundMax)
        ti.root.place(self.res)
        ti.root.place(self.camera_pos)
        ti.root.place(self.aspect_ratio)
        ti.root.place(self.lens_z)

        self.aspect_ratio[None] = float(res[0])/res[1]
        self.res = ti.Vector([400, 400])
        self.camera_pos = ti.Vector([*camera_pos])

        self.stratify_res = 5
        self.inv_stratify = 1.0 / 5.0

    @ti.func
    def rear_z(self):
        return self.thickness[elements_count - 1]


    @ti.func
    def recompute_exit_pupil(self):
        """
        pre-process exit pupil of the lens system
        """

        rearRadius = self.curvatureRadius[elements_count - 1]
        rearZ = self.rear_z()
        count = 0
        samples = 1024 * 1024
        half = 1.5 * rearRadius
        proj_bmin, proj_bmax = ti.Vector([-half, half]), ti.Vector([-half, half])
        for i in range(pupil_interval_count):
            r0 = ti.cast(i, ti.float) / pupil_interval_count * self.film_diagnal / 2.0
            r1 = ti.cast(i + 1, ti.float) / pupil_interval_count * self.film_diagnal / 2.0

            bmin, bmax = make_bound2()
            for j in range(samples):
                u = radical_inverse_2(j)
                v = radical_inverse_3(j)
                film_pos = ti.Vector([lerp(ti.cast(j, ti.f32), r0, r1), 0.0, 0.0])
                lens_pos = ti.Vector([lerp(u,-half,half),lerp(v,-half, half), rearZ])
                if inside_aabb(bmin, bmax, lens_pos) or self.gen_ray_from_film(film_pos,(lens_pos - film_pos).normalized()):
                    bmin,bmax = bound_union_with(bmin,bmax,ti.Vector([lens_pos.x, lens_pos.y]))
                    count += 1

            if count == 0:
                bmin, bmax = proj_bmin, proj_bmax

            assert bmax > bmin

            delta = 2 * (bmax-bmin).norm() / ti.sqrt(samples)
            bmin -= delta
            bmax += delta

            self.exitPupilBoundMin[i] = bmin
            self.exitPupilBoundMax[i] = bmax

    @ti.func
    def sample_exit_pupil(self, film_pos, uv):
        """
        Returns the sample point and the area
        """
        assert uv >= 0.0 and uv <= 1.0

        r = film_pos.norm()
        index = ti.min(r / self.film_diagnal * 2.0 * pupil_interval_count, pupil_interval_count - 1)
        bmin, bmax = self.exitPupilBoundMin[index], self.exitPupilBoundMax[index]
        area = (bmax - bmin).dot(ti.Vector([1.0, 1.0]))
        sampled = lerp(uv, bmin, bmax)
        sint = film_pos.y / r if abs(r) < eps else 0.0
        cost = film_pos.x / r if abs(r) < eps else 0.0
        return ti.Vector(
            [
                cost * sampled.x - sint * sampled.y,
                sint * sampled.x + cost * sampled.y,
                self.rear_z()
            ]), area

    @ti.func
    def gen_ray(self, film_uv, lens_uv):
        extent = ti.Vector(
            [ti.static(self.res[0], ti.f32),
            ti.static(self.res[1], ti.f32)]
         )
        film_pos = lerp(film_uv, ti.Vector([0.0,0.0]), extent)
        film_pos = film_pos - extent / 2.0
        lens_pos, area = self.sample_exit_pupil(film_pos, lens_uv)
        film_pos = ti.Vector([extent.x, extent.y, 0.0])
        r, d = film_pos, lens_pos - film_pos
        exit, out_r ,out_d = self.gen_ray_from_film(r, d)
        if not exit:
            return area

        # translate the ray from cameray space into world space
        return out_r, out_d


    @ti.func
    def compute_cardinal_points(self, in_ro, out_ro, out_rd):
        """
        Returns the z coordinate of the principal plane the the focal point
        (fz, pz)
        note: these vector are in camera space
        """
        tf = -out_ro.x / out_rd.x
        tp = (in_ro.x - out_ro.x) / out_rd.x
        return (out_ro + out_rd * tf).z, (out_ro + out_rd * tp).z


    @ti.func
    def compute_thick_lens_approximation(self):
        """
        Returns the focal length and the z of principal plane
        return fz1, pz1, fz2, pz2
        """
        x = 0.1
        so = ti.Vector([x, 0.0, self.lensZ() + 1.0])
        sd = ti.Vector([0.0,0.0,-1.0])
        fo = ti.Vector([x, 0.0, self.thickness[self.thickness.n - 1] - 1.0])
        fd = ti.Vector([0.0,0.0,1.0])
        o1, d1 = self.gen_ray_from_scene(so, sd)
        o2, d2 = self.gen_ray_from_film(fo, fd)
        return self.compute_cardinal_points(so, o1, d1), self.compute_cardinal_points(fo, o2, d2)


    @ti.func
    def focus_thick_camera(self, focus_distance):
        """
        focus_distance > 0
        """
        fz1, pz1, fz2, pz2 = self.compute_thick_lens_approximation()
        f = fz1 - pz1
        assert f > 0
        z = -focus_distance
        delta = 0.5 * (pz2 - z + pz1 - ti.sqrt((pz2 - z - pz1)*(pz2-z-4*f-pz1) ))
        return self.thickness[self.thickness.n - 1] + delta

    @ti.func
    def intersect_with_sphere(self,
                            center,
                            radius,
                            ro,
                            rd):
        """
        A specialization for evaluating the intersection of ray and sphere which center is along z-axis
        Returns the ray paramter t and the intersection normal
        """

        t = 0.0
        o = ro - ti.Vector([0.0,0.0,center])

        # translate the sphere to original
        A = rd.x * rd.x + rd.y * rd.y + rd.z * rd.z
        B = 2 * ( rd.x * ro.x + rd.y * ro.y + rd.z * ro.z)
        C = ro.x * ro.x + ro.y * ro.y + ro.z * ro.z - radius * radius
        delta = B * B - 4 * A * C
        if delta < 0:
            return False, 0.0, ti.Vector([0.0, 0.0, 0.0])

        t0 = (-B + ti.sqrt(delta))/ (2*A)
        t1 = (-B - ti.sqrt(delta))/ (2*A)

        closer = (rd.z > 0) ^ (radius < 0)
        t = ti.min(t0,t1) if closer else ti.max(t0,t1)
        if t < 0:
            return False, t, ti.Vector([0.0,0.0,0.0])

        n = (o + t * rd).normalized()
        n = -n if ti.dot(n, rd) <0.0 else n
        return True, t, n

    @ti.func
    def lensZ(self):
        z = 0.0
        for i in self.thickness:
            z += self.thickness[i]
        return z

    @ti.func
    def gen_ray_from_scene(self, ori, dir):
        ro, rd = ti.Vector([ori.x, ori.y, -ori.z]), ti.Vector([dir.x, dir.y, -dir.z])
        elemZ = self.lensZ()

        for i in ti.static(range(elements_count)):
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
    def gen_ray_from_film(self, ori, dir):
        """
        Input ray is the initial ray sampled from film to the rear lens element.
        Returns True and the output ray if the ray could be pass the lens system
        or returns False
        """
        ro, rd = ti.Vector([ori.x, ori.y, -ori.z]), ti.Vector([dir.x, dir.y, -dir.z])
        elemZ = 0.0
        for i in ti.static(range(elements_count - 1, -1, -1)):
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
