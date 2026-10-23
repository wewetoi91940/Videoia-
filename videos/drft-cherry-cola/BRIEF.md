---
workflow: motion-graphics
flow: automation
storyboard: no
message: "DRFT Cherry Cola — Break the ordinary."
destination: social vertical
aspect: "9:16"
canvas: 1080x1920
fps: 30
length: 10s
language: fr (on-screen copy in English, as supplied)
audience: premium soft-drink ad viewers
---

# DRFT CHERRY COLA — ultra-satisfying 10s product sting

## Intent

A sensory, not-a-classic-ad experience around a fictional premium soda can.
Satisfaction comes from precision: perfect alignment, fluid rotation, tension,
release, matter, rhythm, invisible transitions. The viewer should want to
rewatch it.

## Storyboard (user-specified, locked)

| #  | Window      | Beat                                                                 |
| -- | ----------- | -------------------------------------------------------------------- |
| S1 | 0.0 – 1.5s  | Magnetic alignment: red lines converge, metal fragments lock into a can on the beat |
| S2 | 1.5 – 3.0s  | Perfect rotation: the can spins, a red light band reveals the label, DRFT stops facing camera |
| S3 | 3.0 – 4.5s  | Liquid precision: red reflection fills the screen; a cola ribbon wraps the can in a ring; drops detach |
| S4 | 4.5 – 6.5s  | The snap: drops freeze, the can contracts in perspective and snaps back; drops become rings that lock onto the can |
| S5 | 6.5 – 8.5s  | Cherry cascade: stylized cherries land around the can; a foreground cherry triggers a full-screen red transition |
| S6 | 8.5 – 10.0s | Packshot: DRFT centered, CHERRY COLA, BREAK THE ORDINARY., one last drop and ripple, then stillness |

## Customizations

- Palette: #0A0A0B black · #8F102B deep cherry · #E52B47 bright red · #C6C2BD aluminium · #F5F3F0 cold white.
- Type: two families max — League Gothic (display) + Oswald (labels / slogan).
- Real 3D (Three.js runtime adapter) for the can, liquid, drops, rings and cherries; DOM/GSAP for type and transitions.
- Liquid is a stylized procedural tube (no physics simulation).

## Assets

- Sound: bundled media-use SFX library only (Pixabay Content License), resolved into `.media/`.
  No music or liquid-specific sound exists in the library; none is faked.

## Notes

- Deterministic: the 3D scene is a pure function of HyperFrames time (`hf-seek`); no clocks, no randomness.
- The user asked for an MP4 render plus a self-critique pass fixing the three biggest defects.
