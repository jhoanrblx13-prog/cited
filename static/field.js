const canvas = document.getElementById("field");
const ctx = canvas.getContext("2d");
const pointer = { x: innerWidth / 2, y: innerHeight / 2, active: false };
let dots = [];

function resize() {
  canvas.width = innerWidth;
  canvas.height = innerHeight;
  dots = [];
  for (let y = 16; y < canvas.height; y += 26) {
    for (let x = 16; x < canvas.width; x += 26) dots.push({ x, y, h: 0 });
  }
}
addEventListener("resize", resize);
addEventListener("pointermove", (event) => {
  pointer.x = event.clientX;
  pointer.y = event.clientY;
  pointer.active = true;
});
addEventListener("pointerleave", () => { pointer.active = false; });
resize();

function frame() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (const dot of dots) {
    const dx = pointer.x - dot.x;
    const dy = pointer.y - dot.y;
    const target = pointer.active ? Math.max(0, 1 - Math.hypot(dx, dy) / 170) : 0;
    dot.h += (target - dot.h) * 0.12;
    ctx.beginPath();
    ctx.fillStyle = `rgba(230,230,230,${0.14 + dot.h * 0.7})`;
    ctx.arc(dot.x - dx * dot.h * 0.16, dot.y - dy * dot.h * 0.16, 1.1 + dot.h * 2.2, 0, Math.PI * 2);
    ctx.fill();
  }
  requestAnimationFrame(frame);
}
frame();
