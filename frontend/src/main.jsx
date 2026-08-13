import React, {useEffect, useRef, useState} from "react";
import {createRoot} from "react-dom/client";
import "./style.css";

const NOTES = ["DÓ","DÓ♯","RÉ","RÉ♯","MI","FÁ","FÁ♯","SOL","LÁ","SI"];
const KEYS = ["1","2","3","4","5","6","7","8","9","0"];

function App(){
  const [songs,setSongs]=useState([]), [selected,setSelected]=useState("");
  const [lights,setLights]=useState(Array(10).fill("off"));
  const [score,setScore]=useState(0), [combo,setCombo]=useState(0);
  const [status,setStatus]=useState("Escolha uma música"), [result,setResult]=useState(null);
  const ws=useRef(null);

  const paint=(button,color)=>setLights(old=>old.map((v,i)=>i===button?color:v));
  const press=(button)=>{ if(ws.current?.readyState===1) ws.current.send(JSON.stringify({type:"press",button})); };

  useEffect(()=>{
    fetch("/api/songs").then(r=>r.json()).then(data=>{setSongs(data); if(data[0]) setSelected(data[0].id)});
    const socket=new WebSocket(`${location.protocol==="https:"?"wss":"ws"}://${location.host}/ws`); ws.current=socket;
    socket.onmessage=({data})=>{
      const m=JSON.parse(data);
      if(m.type==="countdown") setStatus(String(m.value));
      if(m.type==="started"){setStatus("VALENDO!"); setScore(0); setCombo(0); setResult(null)}
      if(m.type==="note") paint(m.button,"blue");
      if(m.type==="note_off") paint(m.button,"off");
      if(m.type==="feedback" && m.result==="hit"){paint(m.button,"green");setScore(m.score);setCombo(m.combo);setStatus(`+${m.points}`)}
      if(m.type==="feedback" && m.result==="wrong"){paint(m.button,"red");setStatus("BOTÃO ERRADO")}
      if(m.type==="feedback" && m.result==="miss"){paint(m.button,"red");setCombo(0);setStatus("PERDEU A NOTA")}
      if(m.type==="finished"){setLights(Array(10).fill("off"));setStatus("RODADA FINALIZADA");setResult(m)}
    };
    const keydown=e=>{const i=KEYS.indexOf(e.key); if(i>=0 && !e.repeat) press(i)};
    addEventListener("keydown",keydown); return()=>{removeEventListener("keydown",keydown);socket.close()};
  },[]);

  const start=()=>ws.current?.send(JSON.stringify({type:"start",song:selected}));
  return <main>
    <header><div><small>RASPBERRY PI 5</small><h1>DESAFIO MUSICAL</h1></div><div className="score"><span>PONTOS</span><b>{score}</b><span>COMBO × {combo}</span></div></header>
    <section className="panel">
      <label>MÚSICA</label><select value={selected} onChange={e=>setSelected(e.target.value)}>{songs.map(s=><option key={s.id} value={s.id}>{s.title}</option>)}</select>
      <button className="start" onClick={start} disabled={!selected}>INICIAR RODADA</button>
    </section>
    <div className="status">{status}</div>
    <section className="buttons">{NOTES.map((note,i)=><button key={note} className={`music ${lights[i]}`} onPointerDown={()=>press(i)}><span>{KEYS[i]}</span><b>{note}</b></button>)}</section>
    {result&&<section className="result"><h2>Resultado</h2><b>{result.score} pontos</b><p>{result.hits} acertos · {result.misses} erros · {result.total} notas</p></section>}
    <footer>Modo simulador: use as teclas 1 a 0</footer>
  </main>
}
createRoot(document.getElementById("root")).render(<App/>);

