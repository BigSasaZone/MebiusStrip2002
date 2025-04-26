import pygame
import pygame.gfxdraw
import math
import colorsys

def vector_sub(a, b):
    return Vector3(a.x - b.x, a.y - b.y, a.z - b.z)

def vector_cross(a, b):
    return Vector3(
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x
    )

def vector_dot(a, b):
    return a.x * b.x + a.y * b.y + a.z * b.z

def vector_length(v):
    return math.sqrt(v.x**2 + v.y**2 + v.z**2)

def vector_normalize(v):
    l = vector_length(v)
    if l == 0:
        return Vector3(0, 0, 0)
    return Vector3(v.x / l, v.y / l, v.z / l)

class Vector3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def rotate_x(self, angle):
        return Vector3(
            self.x,
            self.y * math.cos(angle) - self.z * math.sin(angle),
            self.y * math.sin(angle) + self.z * math.cos(angle)
        )

    def rotate_y(self, angle):
        return Vector3(
            self.x * math.cos(angle) + self.z * math.sin(angle),
            self.y,
            -self.x * math.sin(angle) + self.z * math.cos(angle)
        )

    def translate(self, other):
        return Vector3(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z
        )

    def __mul__(self, scalar):
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

# ------------------- КЛАСС КАМЕРЫ -------------------
class Camera:
    def __init__(self):
        self.position = Vector3(0, 0, 5)
        self.rotation = Vector3(0, 0, 0)
        self.move_speed = 0.1
        self.rotate_speed = 0.05

    def update(self, keys, dt):
        if keys[pygame.K_LEFT]:
            self.rotation.y -= self.rotate_speed
        if keys[pygame.K_RIGHT]:
            self.rotation.y += self.rotate_speed
        if keys[pygame.K_UP]:
            self.rotation.x += self.rotate_speed
        if keys[pygame.K_DOWN]:
            self.rotation.x -= self.rotate_speed
        self.rotation.x = max(-math.pi/2, min(math.pi/2, self.rotation.x))

        forward = Vector3(
            math.sin(self.rotation.y),
            -math.sin(self.rotation.x),
            math.cos(self.rotation.y)
        )
        right = Vector3(
            math.cos(self.rotation.y),
            0,
            -math.sin(self.rotation.y)
        )

        if keys[pygame.K_w]:
            self.position = self.position.translate(forward * self.move_speed)
        if keys[pygame.K_s]:
            self.position = self.position.translate(forward * -self.move_speed)
        if keys[pygame.K_a]:
            self.position = self.position.translate(right * -self.move_speed)
        if keys[pygame.K_d]:
            self.position = self.position.translate(right * self.move_speed)
        if keys[pygame.K_q]:
            self.position.y += self.move_speed
        if keys[pygame.K_e]:
            self.position.y -= self.move_speed

class MobiusStrip:
    def __init__(self, u_res=64, v_res=16):
        self.alpha = 1.0
        self.beta = 0.5
        self.u_res = u_res
        self.v_res = v_res
        self.grid = []
        self.generate()

    def generate(self):
        self.grid = []
        for iu in range(self.u_res + 1):
            u = 2 * math.pi * iu / self.u_res
            row = []
            for iv in range(self.v_res):
                v = (iv / (self.v_res - 1)) - 0.5
                x = (self.alpha + v * math.cos(u / 2)) * math.cos(u)
                y = (self.alpha + v * math.cos(u / 2)) * math.sin(u)
                z = self.beta * v * math.sin(u / 2)
                row.append(Vector3(x, y, z))
            self.grid.append(row)

class Slider:
    def __init__(self, x, y, min_val, max_val, step, initial):
        self.rect = pygame.Rect(x, y, 200, 20)
        self.min = min_val
        self.max = max_val
        self.step = step
        self.value = initial
        self.dragging = False

    def update(self, mouse_pos, mouse_down):
        if mouse_down and self.rect.collidepoint(mouse_pos):
            self.dragging = True
        if not mouse_down:
            self.dragging = False
        if self.dragging:
            self.value = ((mouse_pos[0] - self.rect.x) / self.rect.width *
                          (self.max - self.min) + self.min)
            self.value = round(self.value / self.step) * self.step

    def draw(self, surface, font):
        pygame.draw.rect(surface, (200, 200, 200), self.rect)
        handle_x = int((self.value - self.min) / (self.max - self.min) * self.rect.width) + self.rect.x
        pygame.draw.circle(surface, (50, 50, 50), (handle_x, self.rect.centery), 10)
        text = font.render(f"{self.value:.1f}", True, (0, 0, 0))
        surface.blit(text, (self.rect.x + self.rect.width + 10, self.rect.y))

def dynamic_color(time_elapsed, intensity):
    h = (time_elapsed * 0.2) % 1.0
    r, g, b = colorsys.hsv_to_rgb(h, 1, 1)
    base = (int(r * 255), int(g * 255), int(b * 255))
    return tuple(min(255, max(0, int(c * intensity))) for c in base)

class Renderer:
    def __init__(self, width=800, height=600):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 18, bold=True)

        self.camera = Camera()
        self.mobius = MobiusStrip()

        self.sliders = {
            'alpha': Slider(20, 20, 1.0, 3.0, 0.2, 1.0),
            'beta': Slider(20, 60, 0.5, 2.0, 0.1, 0.5),
            'u_res': Slider(20, 100, 16, 128, 16, 64)
        }

        self.light_dir = vector_normalize(Vector3(-1, -1, -1))
        self.start_time = pygame.time.get_ticks()
        self.bg_surface = pygame.Surface((width, height))
        self.create_gradient_background()
        self.ui_panel = pygame.Surface((200, height))
        self.ui_panel.fill((240, 240, 240))

    def create_gradient_background(self):
        top_color = (173, 216, 230)
        bottom_color = (255, 255, 255)
        for y in range(self.height):
            ratio = y / self.height
            r = top_color[0] * (1 - ratio) + bottom_color[0] * ratio
            g = top_color[1] * (1 - ratio) + bottom_color[1] * ratio
            b = top_color[2] * (1 - ratio) + bottom_color[2] * ratio
            pygame.draw.line(self.bg_surface, (int(r), int(g), int(b)), (0, y), (self.width, y))

    def project_with_depth(self, point):
        translated = Vector3(
            point.x - self.camera.position.x,
            point.y - self.camera.position.y,
            point.z - self.camera.position.z
        )
        rotated = translated.rotate_x(-self.camera.rotation.x).rotate_y(-self.camera.rotation.y)
        if rotated.z <= 0:
            return None, None
        fov = 256
        scale = fov / rotated.z
        x = int(self.width / 2 + rotated.x * scale)
        y = int(self.height / 2 - rotated.y * scale)
        return (x, y), rotated.z

    def draw_mobius(self, time_elapsed):
        grid = self.mobius.grid
        u_res = len(grid) - 1
        v_res = len(grid[0])

        triangles = []
        for i in range(u_res):
            for j in range(v_res - 1):
                p0 = grid[i][j]
                p1 = grid[i + 1][j]
                p2 = grid[i + 1][j + 1]
                p3 = grid[i][j + 1]
                triangles.append((p0, p1, p2))
                triangles.append((p0, p2, p3))

        render_tris = []
        for tri in triangles:
            proj = []
            depths = []
            skip = False
            for p in tri:
                pos, depth = self.project_with_depth(p)
                if pos is None:
                    skip = True
                    break
                proj.append(pos)
                depths.append(depth)
            if skip:
                continue

            v1 = vector_sub(tri[1], tri[0])
            v2 = vector_sub(tri[2], tri[0])
            normal = vector_normalize(vector_cross(v1, v2))

            ambient = 0.3
            intensity = ambient + (1 - ambient) * max(0, vector_dot(normal, self.light_dir))
            color = dynamic_color(time_elapsed, intensity)

            avg_depth = sum(depths) / 3
            render_tris.append((avg_depth, proj, color))

        render_tris.sort(key=lambda x: x[0], reverse=True)

        for _, proj, color in render_tris:
            pygame.gfxdraw.filled_polygon(self.screen, proj, color)
            pygame.gfxdraw.aapolygon(self.screen, proj, color)

    def draw_overlay(self):
        text = self.font.render("ESC - Exit", True, (0, 0, 0))
        self.screen.blit(text, (20, self.height - 60))

    def draw_ui_panel(self):
        self.ui_panel.fill((240, 240, 240))
        title = self.font.render("Панель управления", True, (0, 0, 0))
        self.ui_panel.blit(title, (10, 10))
        alpha_text = self.font.render(f"Alpha: {self.mobius.alpha:.1f}", True, (0, 0, 0))
        beta_text = self.font.render(f"Beta: {self.mobius.beta:.1f}", True, (0, 0, 0))
        u_res_text = self.font.render(f"U Res: {self.mobius.u_res}", True, (0, 0, 0))
        self.ui_panel.blit(alpha_text, (10, 50))
        self.ui_panel.blit(beta_text, (10, 80))
        self.ui_panel.blit(u_res_text, (10, 110))
        instr1 = self.font.render("WASD - Move", True, (0, 0, 0))
        instr2 = self.font.render("Arrows - Rotate", True, (0, 0, 0))
        self.ui_panel.blit(instr1, (10, 150))
        self.ui_panel.blit(instr2, (10, 180))
        self.screen.blit(self.ui_panel, (self.width - 200, 0))

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            time_elapsed = (pygame.time.get_ticks() - self.start_time) / 1000.0

            mouse_down = False
            mouse_pos = (0, 0)
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_down = True
                mouse_pos = pygame.mouse.get_pos()

            for slider in self.sliders.values():
                slider.update(mouse_pos, mouse_down)

            new_alpha = self.sliders['alpha'].value
            new_beta = self.sliders['beta'].value
            new_u_res = int(self.sliders['u_res'].value)
            
            if (new_alpha != self.mobius.alpha or 
                new_beta != self.mobius.beta or 
                new_u_res != self.mobius.u_res):
                
                self.mobius.alpha = new_alpha
                self.mobius.beta = new_beta
                self.mobius.u_res = new_u_res
                self.mobius.generate()

            self.camera.update(pygame.key.get_pressed(), dt)
            self.screen.blit(self.bg_surface, (0, 0))
            self.draw_mobius(time_elapsed)
            for slider in self.sliders.values():
                slider.draw(self.screen, self.font)
            self.draw_overlay()
            self.draw_ui_panel()

            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    Renderer().run()
