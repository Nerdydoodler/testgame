import math
import random
import sys

import pygame


WIDTH = 800
HEIGHT = 600
FPS = 60

PLAYER_SPEED = 280.0
PLAYER_SLOW_MULT = 0.45
PLAYER_RADIUS = 10

PLAYER_BULLET_SPEED = 520.0
PLAYER_BULLET_RADIUS = 4
PLAYER_SHOT_COOLDOWN = 0.09

SUPER_BULLET_SPEED = 420.0
SUPER_BULLET_RADIUS = 18

ENEMY_RADIUS = 18
ENEMY_BULLET_SPEED = 220.0
ENEMY_BULLET_RADIUS = 5

BOSS_MAX_HP = 100
MAX_HP = 20
SUPER_DAMAGE = 20
SUPER_COOLDOWN = 3.0


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def dist2(ax, ay, bx, by):
    dx = ax - bx
    dy = ay - by
    return dx * dx + dy * dy


class Player:
    def __init__(self):
        self.x = WIDTH * 0.5
        self.y = HEIGHT * 0.82
        self.hp = MAX_HP
        self.shot_cd = 0.0
        self.super_cd = 0.0

    def reset(self):
        self.x = WIDTH * 0.5
        self.y = HEIGHT * 0.82
        self.hp = MAX_HP
        self.shot_cd = 0.0
        self.super_cd = 0.0

    def update(self, dt, keys):
        speed = PLAYER_SPEED
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            speed *= PLAYER_SLOW_MULT

        dx = 0.0
        dy = 0.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1.0

        if dx != 0.0 or dy != 0.0:
            inv = 1.0 / math.sqrt(dx * dx + dy * dy)
            dx *= inv
            dy *= inv

        self.x += dx * speed * dt
        self.y += dy * speed * dt

        pad = PLAYER_RADIUS + 6
        self.x = clamp(self.x, pad, WIDTH - pad)
        self.y = clamp(self.y, pad, HEIGHT - pad)

        self.shot_cd = max(0.0, self.shot_cd - dt)
        self.super_cd = max(0.0, self.super_cd - dt)

    def can_shoot(self):
        return self.shot_cd <= 0.0

    def shoot(self):
        self.shot_cd = PLAYER_SHOT_COOLDOWN

    def can_super(self):
        return self.super_cd <= 0.0

    def use_super(self):
        self.super_cd = SUPER_COOLDOWN


class Enemy:
    def __init__(self):
        self.x = WIDTH * 0.5
        self.y = HEIGHT * 0.22
        self.t = 0.0
        self.base_x = self.x

    def reset(self):
        self.x = WIDTH * 0.5
        self.y = HEIGHT * 0.22
        self.t = 0.0
        self.base_x = self.x

    def update(self, dt):
        self.t += dt
        self.x = self.base_x + math.sin(self.t * 0.9) * 220.0


class Bullet:
    def __init__(self, x, y, vx, vy, radius, friendly, damage=1):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.friendly = friendly
        self.damage = damage
        self.dead = False

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        if (
            self.x < -40
            or self.x > WIDTH + 40
            or self.y < -60
            or self.y > HEIGHT + 60
        ):
            self.dead = True


def spawn_player_bullets(player, bullets):
    bullets.append(
        Bullet(
            player.x,
            player.y - 12,
            0.0,
            -PLAYER_BULLET_SPEED,
            PLAYER_BULLET_RADIUS,
            True,
            1,
        )
    )


def spawn_super_bullet(player, bullets):
    bullets.append(
        Bullet(
            player.x,
            player.y - 18,
            0.0,
            -SUPER_BULLET_SPEED,
            SUPER_BULLET_RADIUS,
            True,
            SUPER_DAMAGE,
        )
    )


def spawn_enemy_pattern(enemy, player, bullets, t_global):
    ring_period = 1.25
    aimed_period = 0.42

    if int((t_global - 0.0) / ring_period) != int((t_global - 0.016) / ring_period):
        n = 24
        base = t_global * 1.6
        for i in range(n):
            ang = base + (i / n) * math.tau
            vx = math.cos(ang) * ENEMY_BULLET_SPEED
            vy = math.sin(ang) * ENEMY_BULLET_SPEED
            bullets.append(Bullet(enemy.x, enemy.y, vx, vy, ENEMY_BULLET_RADIUS, False, 1))

    if int((t_global - 0.0) / aimed_period) != int((t_global - 0.016) / aimed_period):
        dx = player.x - enemy.x
        dy = player.y - enemy.y
        d = math.hypot(dx, dy)
        if d > 0.001:
            dx /= d
            dy /= d
        spread = 0.18
        for s in (-spread, 0.0, spread):
            ang = math.atan2(dy, dx) + s
            vx = math.cos(ang) * (ENEMY_BULLET_SPEED * 1.15)
            vy = math.sin(ang) * (ENEMY_BULLET_SPEED * 1.15)
            bullets.append(Bullet(enemy.x, enemy.y, vx, vy, ENEMY_BULLET_RADIUS, False, 1))


def draw_text_center(surface, font, text, y, color):
    img = font.render(text, True, color)
    rect = img.get_rect(center=(WIDTH // 2, int(y)))
    surface.blit(img, rect)


def reset_game(player, enemy):
    player.reset()
    enemy.reset()
    return [], [], 0.0, BOSS_MAX_HP


def main():
    pygame.init()
    pygame.display.set_caption("Bullet Hell")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 28)
    big_font = pygame.font.SysFont(None, 72)

    player = Player()
    enemy = Enemy()

    player_bullets = []
    enemy_bullets = []
    t_global = 0.0
    boss_hp = BOSS_MAX_HP

    state = "playing"

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 1.0 / 20.0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_p and state not in ("game_over", "win"):
                    state = "paused" if state == "playing" else "playing"
                if event.key == pygame.K_x and state == "playing":
                    if boss_hp > 0 and player.can_super():
                        spawn_super_bullet(player, player_bullets)
                        player.use_super()
                if state in ("game_over", "win") and event.key == pygame.K_r:
                    player_bullets, enemy_bullets, t_global, boss_hp = reset_game(player, enemy)
                    state = "playing"

        keys = pygame.key.get_pressed()

        if state == "playing":
            t_global += dt
            player.update(dt, keys)
            enemy.update(dt)

            if (keys[pygame.K_z] or keys[pygame.K_SPACE]) and player.can_shoot():
                player.shoot()
                spawn_player_bullets(player, player_bullets)

            if boss_hp > 0:
                spawn_enemy_pattern(enemy, player, enemy_bullets, t_global)

            for b in player_bullets:
                b.update(dt)
                if not b.dead:
                    if dist2(b.x, b.y, enemy.x, enemy.y) <= (b.radius + ENEMY_RADIUS) ** 2:
                        b.dead = True
                        boss_hp = max(0, boss_hp - b.damage)

            for b in enemy_bullets:
                b.update(dt)
                if not b.dead:
                    if dist2(b.x, b.y, player.x, player.y) <= (b.radius + PLAYER_RADIUS) ** 2:
                        b.dead = True
                        player.hp = max(0, player.hp - 1)

            player_bullets = [b for b in player_bullets if not b.dead]
            enemy_bullets = [b for b in enemy_bullets if not b.dead]

            if boss_hp <= 0:
                state = "win"

            if player.hp <= 0:
                state = "game_over"

        screen.fill((10, 10, 14))

        pygame.draw.circle(screen, (220, 80, 80), (int(enemy.x), int(enemy.y)), ENEMY_RADIUS)

        for b in player_bullets:
            if b.damage >= SUPER_DAMAGE:
                pygame.draw.circle(screen, (60, 150, 255), (int(b.x), int(b.y)), b.radius)
            else:
                pygame.draw.circle(screen, (110, 200, 255), (int(b.x), int(b.y)), b.radius)

        for b in enemy_bullets:
            pygame.draw.circle(screen, (255, 200, 90), (int(b.x), int(b.y)), b.radius)

        px = int(player.x)
        py = int(player.y)
        pygame.draw.polygon(
            screen,
            (120, 255, 140),
            [(px, py - 14), (px - 10, py + 12), (px + 10, py + 12)],
        )
        pygame.draw.circle(screen, (40, 40, 40), (px, py), 3)

        hp_text = font.render(f"HP: {player.hp}/{MAX_HP}", True, (235, 235, 235))
        screen.blit(hp_text, (16, 14))

        bar_x = 16
        bar_y = 42
        bar_w = 220
        bar_h = 12
        pygame.draw.rect(screen, (30, 30, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        fill_w = int(bar_w * (player.hp / MAX_HP))
        pygame.draw.rect(screen, (90, 220, 120), (bar_x, bar_y, fill_w, bar_h), border_radius=3)

        if player.super_cd <= 0.0 and state == "playing":
            super_text = font.render("SUPER (X): READY", True, (235, 235, 235))
            screen.blit(super_text, (16, 62))

        boss_bar_x = 16
        boss_bar_w = WIDTH - 32
        boss_bar_h = 22
        boss_bar_y = HEIGHT - 16 - boss_bar_h
        pygame.draw.rect(
            screen,
            (35, 18, 18),
            (boss_bar_x, boss_bar_y, boss_bar_w, boss_bar_h),
            border_radius=6,
        )
        boss_fill_w = int(boss_bar_w * (boss_hp / BOSS_MAX_HP))
        pygame.draw.rect(
            screen,
            (220, 45, 45),
            (boss_bar_x, boss_bar_y, boss_fill_w, boss_bar_h),
            border_radius=6,
        )
        pygame.draw.rect(
            screen,
            (120, 60, 60),
            (boss_bar_x, boss_bar_y, boss_bar_w, boss_bar_h),
            width=2,
            border_radius=6,
        )

        boss_text = font.render(f"BOSS HP: {boss_hp}/{BOSS_MAX_HP}", True, (235, 235, 235))
        screen.blit(boss_text, (boss_bar_x + 10, boss_bar_y - 22))

        if state == "paused":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            draw_text_center(screen, big_font, "PAUSED", HEIGHT * 0.45, (255, 255, 255))
            draw_text_center(screen, font, "Press P to Resume", HEIGHT * 0.56, (220, 220, 220))

        if state == "game_over":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            screen.blit(overlay, (0, 0))
            draw_text_center(screen, big_font, "GAME OVER", HEIGHT * 0.42, (255, 255, 255))
            draw_text_center(screen, font, "Press R to Restart", HEIGHT * 0.54, (220, 220, 220))
            draw_text_center(screen, font, "Esc to Quit", HEIGHT * 0.60, (220, 220, 220))

        if state == "win":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            draw_text_center(screen, big_font, "YOU WIN", HEIGHT * 0.42, (255, 255, 255))
            draw_text_center(screen, font, "Press R to Restart", HEIGHT * 0.54, (220, 220, 220))
            draw_text_center(screen, font, "Esc to Quit", HEIGHT * 0.60, (220, 220, 220))

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
