"""
Referencia: Tech With Tim
Modificado por: Nuno Morbey e Hugo Pereira
"""

import pygame
import random
import os
import time
import neat
import visualize

pygame.font.init()

WIN_WIDTH = 600
WIN_HEIGHT = 800
FLOOR = 730
STAT_FONT = pygame.font.SysFont("comicsans", 20)
END_FONT = pygame.font.SysFont("comicsans", 70)
DRAW_LINES = False

WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird")

pipe_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")).convert_alpha())
bg_img = pygame.transform.scale(pygame.image.load(os.path.join("imgs","bg.png")).convert_alpha(), (600, 900))
bird_images = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird" + str(x) + ".png"))) for x in range(1,4)]
base_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")).convert_alpha())

gen = 0

class Bird:
    """
	Classe Bird que representa o pássaro do Flappy Bird
	"""
    MAX_ROTATION = 25
    IMGS = bird_images
    ROT_VEL = 20
    ANIMATION_TIME = 1

    def __init__(self, x, y):
        """
        Inicializa o objeto
        :param x: posição inicial x (int)
        :param y: posição inicial y (int)
        :return: None
        """
        self.x = x
        self.y = y
        self.tilt = 0  # degrees to tilt
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        """
        Faz o pássaro pular
        
        """
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        """
        Faz o pássaro se mover
        
        """
        self.tick_count += 1

        # para aceleração descendente
        displacement = self.vel*(self.tick_count) + 0.5*(3)*(self.tick_count)**2  # calculate displacement

       # velocidade terminal
        if displacement >= 16:
            displacement = (displacement/abs(displacement)) * 16

        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        if displacement < 0 or self.y < self.height + 50:  # tilt up
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:  # inclinação para baixo
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        """
        Desenha o pássaro
        :param win: janela ou superfície do pygame
        :return: None
        """
        self.img_count += 1

        # Para animação do pássaro, alterna entre três imagens
        if self.img_count <= self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count <= self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count <= self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count <= self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # para que o pássaro não bata as asas ao mergulhar
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2


        # inclina o pássaro
        blitRotateCenter(win, self.img, (self.x, self.y), self.tilt)

    def get_mask(self):
        """
        Obtém a máscara para a imagem atual do pássaro
        
        """
        return pygame.mask.from_surface(self.img)


class Pipe():
    """
    Representa como objeto o cano
    """
    GAP = 200
    VEL = 9

    def __init__(self, x):
        """
        Inicializa o objeto de cano
        :param x: int
        :param y: int
        :return" None
        """
        self.x = x
        self.height = 0

        # onde está o topo e a base do cano
        self.top = 0
        self.bottom = 0

        self.PIPE_TOP = pygame.transform.flip(pipe_img, False, True)
        self.PIPE_BOTTOM = pipe_img

        self.passed = False

        self.set_height()

    def set_height(self):
        """
        Define a altura do cano, a partir do topo da tela
        """
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        """
        Move o cano com base na velocidade
        """
        self.x -= self.VEL

    def draw(self, win):
        """
        Desenha o cano de cima e o cano de baixo
        :param win: janela/superfície do pygame
        """
        # desenha o topo
        win.blit(self.PIPE_TOP, (self.x, self.top))
        # desenha o de baixo
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))


    def collide(self, bird, win):
        """
        Verifica se um ponto está colidindo com o cano
        :param bird: objeto Bird
        :return: Bool
        """
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask,top_offset)

        if b_point or t_point:
            return True

        return False

class Base:
    """
   Representa o chão móvel do jogo
    """
    VEL = 10
    WIDTH = base_img.get_width()
    IMG = base_img

    def __init__(self, y):
        """
        Inicializa o objeto
        :param y: int
        """
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        """
        Move o chão para dar a sensação de rolagem
        """
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        """
        Desenha o chão. São duas imagens que se movem juntas.
        :param win: superfície/janela do pygame
        """
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def blitRotateCenter(surf, image, topleft, angle):
    """
    Rotaciona uma superfície e a blita na janela
    :param surf: a superfície para blitar
    :param image: a superfície da imagem a ser rotacionada
    :param topleft: a posição superior esquerda da imagem
    :param angle: um valor de ângulo float
    """
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center = image.get_rect(topleft = topleft).center)

    surf.blit(rotated_image, new_rect.topleft)

def draw_window(win, birds, pipes, base, score, gen, pipe_ind):
    """
    Desenha a janela para o loop principal do jogo
    :param win: superfície da janela do pygame
    :param birds: objeto Bird
    :param pipes: lista de canos
    :param base: objeto Base
    :param score: pontuação do jogo (int)
    :param gen: geração atual
    :param pipe_ind: índice do cano mais próximo
    """
    if gen == 0:
        gen = 1
    win.blit(bg_img, (0,0))

    for pipe in pipes:
        pipe.draw(win)

    base.draw(win)
    for bird in birds:
        # desenha linhas do pássaro ao cano
        if DRAW_LINES:
            try:
                pygame.draw.line(win, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width()/2, pipes[pipe_ind].height), 5)
                pygame.draw.line(win, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width()/2, pipes[pipe_ind].bottom), 5)
            except:
                pass
        # desenha o pássaro
        bird.draw(win)

    # score
    score_label = STAT_FONT.render("Score: " + str(score),1,(255,255,255))
    win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 15, 10))

    # gerações
    score_label = STAT_FONT.render("Geração: " + str(gen-1),1,(255,255,255))
    win.blit(score_label, (10, 10))

    # vivos
    score_label = STAT_FONT.render("Vivos: " + str(len(birds)),1,(255,255,255))
    win.blit(score_label, (10, 50)) # x e o y do texto

    pygame.display.update()


def eval_genomes(genomes, config):
    """
    Executa a simulação da população atual de pássaros e define sua aptidão com base na distância que alcançam no jogo.
    """
    global WIN, gen
    win = WIN
    gen += 1

    # Comece criando listas que contenham o próprio genoma, a
    # rede neural associada ao genoma e
    # o objeto de pássaro que usa essa rede para jogar
    nets = []
    birds = []
    ge = []
    for genome_id, genome in genomes:
        genome.fitness = 0  # start with fitness level of 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230,350))
        ge.append(genome)

    base = Base(FLOOR)
    pipes = [Pipe(700)]
    score = 0

    clock = pygame.time.Clock()

    run = True
    while run and len(birds) > 0:
        clock.tick(1000)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():  # determine whether to use the first or second
                pipe_ind = 1                                                                 # pipe on the screen for neural network input

        for x, bird in enumerate(birds): # dê a cada pássaro uma aptidão de 0.1 para cada frame que ele permanecer vivo
            ge[x].fitness += 0.1
            bird.move()

            # enviar a localização do pássaro, a localização do cano superior e a localização do cano inferior e determinar pela rede neural se deve pular ou não
            output = nets[birds.index(bird)].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:  # usamos uma função de ativação tangente hiperbólica, portanto, o resultado estará entre -1 e 1. se for maior que 0,5, ele dá jump
                bird.jump()



        base.move()

        rem = []
        add_pipe = False
        for pipe in pipes:
            pipe.move()
            # verificar colisão
            for bird in birds:
                if pipe.collide(bird, win):
                    ge[birds.index(bird)].fitness -= 1
                    nets.pop(birds.index(bird))
                    ge.pop(birds.index(bird))
                    birds.pop(birds.index(bird))

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

        if add_pipe:
            score += 1
            
            for genome in ge:
                genome.fitness += 1 #mexer aqui
            pipes.append(Pipe(WIN_WIDTH))

        for r in rem:
            pipes.remove(r)

        for bird in birds:
            if bird.y + bird.img.get_height() - 10 >= FLOOR or bird.y < -50:
                nets.pop(birds.index(bird))
                ge.pop(birds.index(bird)) #se retirar os birds nao melhoram com a geraçao
                birds.pop(birds.index(bird))

        draw_window(WIN, birds, pipes, base, score, gen, pipe_ind)



def run(config_file):
    """
    Executa o algoritmo NEAT para treinar uma rede neural para jogar Flappy Bird.
    :param config_file: localização do arquivo de configuração
    
    """
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    # Crie a população, que é o objeto de nível superior para uma execução NEAT
    p = neat.Population(config)

    # Adicione um relator de stdout para mostrar o progresso no terminal
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    #p.add_reporter(neat.Checkpointer(5))

    # quantas gerações serão executadas antes de encerrar o jogo
    winner = p.run(eval_genomes, 50)

    # show final stats
    print('\nBest genome:\n{!s}'.format(winner))


if __name__ == '__main__':
    # Determine o caminho para o arquivo de configuração. Essa manipulação de caminho está aqui
    # para que o script seja executado com êxito independentemente do diretório de trabalho atual.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)
