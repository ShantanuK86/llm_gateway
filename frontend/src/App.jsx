import React, { useState, useEffect, useRef } from 'react';
import { User, Shield, Database, Brain, ArrowRight, Zap } from 'lucide-react';
import './index.css';

function App() {
  const [prompt, setPrompt] = useState('What is the capital of France?');
  const [packets, setPackets] = useState([]);
  const [nodesState, setNodesState] = useState({ redis: '', cache: '', llm: '' });
  const [logs, setLogs] = useState([{ id: 1, msg: 'System initialized. Waiting for packets...', type: 'info' }]);
  const [stats, setStats] = useState({ total_cost: 0, total_cached: 0 });
  const [latestResponse, setLatestResponse] = useState('');
  
  const terminalRef = useRef(null);

  const delay = (ms) => new Promise(res => setTimeout(res, ms));

  // Background Stats Poller
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch('http://localhost:8000/v1/gateway/stats');
        const data = await res.json();
        setStats(data);
      } catch (err) {
        // Silent fail on background polling
      }
    };
    fetchStats();
    const interval = setInterval(fetchStats, 1000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll terminal
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  const addLog = (msg, type) => {
    setLogs(prev => {
      const newLogs = [...prev, { id: Date.now() + Math.random(), msg, type }];
      if (newLogs.length > 20) newLogs.shift();
      return newLogs;
    });
  };

  const pulseNode = async (node, className) => {
    setNodesState(prev => ({ ...prev, [node]: className }));
    await delay(300);
    setNodesState(prev => ({ ...prev, [node]: '' }));
  };

  const spawnPacket = async (customPrompt) => {
    const pId = Date.now() + Math.random();
    const packetColor = '#f8fafc';
    
    // Spawn at User
    setPackets(prev => [...prev, { id: pId, status: 'pos-user', color: packetColor, shadow: '#38bdf8' }]);
    await delay(100);
    
    // Fly to Redis
    setPackets(prev => prev.map(p => p.id === pId ? { ...p, status: 'pos-redis' } : p));
    
    const startTime = Date.now();
    try {
      const res = await fetch('http://localhost:8000/v1/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': 'test_api_key_123' },
        body: JSON.stringify({ model: 'gpt-4o', messages: [{ role: 'user', content: customPrompt }] })
      });
      
      const timeMs = Date.now() - startTime;
      await delay(500); // Wait for visual flight

      if (res.status === 429) {
        pulseNode('redis', 'pulse-red');
        setPackets(prev => prev.map(p => p.id === pId ? { ...p, status: 'pos-user', color: '#ef4444', shadow: '#ef4444' } : p));
        addLog(`[429 RATE LIMIT] Blocked at Gateway (${timeMs}ms)`, 'error');
        await delay(500);
        setPackets(prev => prev.filter(p => p.id !== pId));
        return;
      }

      const data = await res.json();
      const xCache = res.headers.get('X-Cache');
      
      pulseNode('redis', 'pulse-green');
      await delay(100);
      
      // Fly to Cache
      setPackets(prev => prev.map(p => p.id === pId ? { ...p, status: 'pos-cache' } : p));
      await delay(500);

      if (xCache === 'HIT') {
        pulseNode('cache', 'pulse-green');
        setPackets(prev => prev.map(p => p.id === pId ? { ...p, status: 'pos-user', color: '#10b981', shadow: '#10b981' } : p));
        addLog(`[CACHE HIT] Vector Match Found (${timeMs}ms)`, 'success');
        await delay(500);
        setLatestResponse(data.choices[0].message.content);
        setPackets(prev => prev.filter(p => p.id !== pId));
        return;
      }

      pulseNode('cache', 'pulse-red');
      await delay(100);
      
      // Fly to LLM
      setPackets(prev => prev.map(p => p.id === pId ? { ...p, status: 'pos-llm' } : p));
      await delay(500);
      
      pulseNode('llm', 'pulse-green');
      setPackets(prev => prev.map(p => p.id === pId ? { ...p, status: 'pos-user', color: '#c084fc', shadow: '#c084fc' } : p));
      addLog(`[CACHE MISS] Executed on LLM (${timeMs}ms)`, 'info');
      await delay(500);
      setLatestResponse(data.choices[0].message.content);
      setPackets(prev => prev.filter(p => p.id !== pId));

    } catch (err) {
      console.error(err);
      addLog(`[ERROR] Connection Failed`, 'error');
      setPackets(prev => prev.filter(p => p.id !== pId));
    }
  };

  const handleSend = () => {
    if (!prompt.trim()) return;
    addLog(`Sending packet...`, 'info');
    setLatestResponse(''); // clear on new send
    spawnPacket(prompt);
  };

  const handleStressTest = async () => {
    addLog(`[STRESS TEST] Firing 6 concurrent packets...`, 'error');
    for (let i = 0; i < 6; i++) {
      spawnPacket(`Stress Test Random ${Math.random()}`);
      await delay(100);
    }
  };

  return (
    <div className="dashboard-wrapper">
      <h1 className="title">Gateway OS</h1>
      
      {/* Floating Mini Metrics */}
      <div className="mini-metrics">
        <div className="metric-pill cache">
          <span className="label">Cache Size</span>
          <span className="value">{stats.total_cached}</span>
        </div>
        <div className="metric-pill cost">
          <span className="label">Live Cost</span>
          <span className="value">${stats.total_cost?.toFixed(6) || '0.000000'}</span>
        </div>
      </div>

      {/* Center Graph */}
      <div className="nodes-grid">
        <svg className="svg-pipes">
          <path d="M 100,450 L 100,100" className="pipe" /> 
          <path d="M 100,100 L 450,100" className="pipe" /> 
          <path d="M 450,100 L 450,450" className="pipe" /> 
          <path d="M 450,450 L 100,450" className="pipe" /> 
          <path d="M 450,100 L 100,450" className="pipe pipe-dashed" /> 
        </svg>

        {packets.map(p => (
          <div 
            key={p.id} 
            className={`packet ${p.status}`} 
            style={{ 
              backgroundColor: p.color, 
              boxShadow: `0 0 15px ${p.color}, 0 0 30px ${p.shadow}` 
            }}
          ></div>
        ))}
        
        <div className="node node-user">
          <div className="icon-core"><User size={28} color="#38bdf8" /></div>
          <h3>User Client</h3>
        </div>
        
        <div className={`node node-redis ${nodesState.redis}`}>
          <div className="icon-core"><Shield size={28} color="#f59e0b" /></div>
          <h3>Redis Gate</h3>
        </div>
        
        <div className={`node node-cache ${nodesState.cache}`}>
          <div className="icon-core"><Database size={28} color="#10b981" /></div>
          <h3>PgVector Cache</h3>
        </div>
        
        <div className={`node node-llm ${nodesState.llm}`}>
          <div className="icon-core"><Brain size={28} color="#c084fc" /></div>
          <h3>Gemini 2.5 Flash</h3>
        </div>
      </div>

      {/* macOS Terminal Logs */}
      <div className="mac-terminal">
        <div className="mac-header">
          <div className="mac-dot red"></div>
          <div className="mac-dot yellow"></div>
          <div className="mac-dot green"></div>
          <div className="mac-title">gateway_trace.log</div>
        </div>
        <div className="terminal-content" ref={terminalRef}>
          {logs.map(log => (
            <div key={log.id} className={`log-entry log-${log.type}`}>
              &gt; {log.msg}
            </div>
          ))}
        </div>
      </div>

      {/* Latest Response Card */}
      <div className={`response-card ${latestResponse ? 'show' : ''}`}>
        <div className="response-header">Latest Output</div>
        <div className="response-content">{latestResponse}</div>
      </div>

      {/* Floating Command Dock */}
      <div className="command-dock">
        <input 
          className="input-box"
          placeholder="Type a prompt to trace..."
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
        />
        <button className="send-btn" onClick={handleSend}>
          Send Packet <ArrowRight size={18} />
        </button>
        <button className="stress-btn" onClick={handleStressTest}>
          <Zap size={18} fill="currentColor" /> Stress (6x)
        </button>
      </div>
    </div>
  );
}

export default App;
