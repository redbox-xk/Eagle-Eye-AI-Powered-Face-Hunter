type Handler = (data: any) => void

class AuraWebSocket {
  private ws: WebSocket | null = null
  private handlers: Map<string, Handler[]> = new Map()
  private reconnectDelay = 1500
  private maxDelay = 30000
  private _connected = false
  private _reconnectTimer: ReturnType<typeof setTimeout> | null = null

  connect() {
    if (this._reconnectTimer) {
      clearTimeout(this._reconnectTimer)
      this._reconnectTimer = null
    }

    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${proto}://${location.host}/ws`

    try {
      this.ws = new WebSocket(url)
    } catch {
      this._scheduleReconnect()
      return
    }

    this.ws.onopen = () => {
      this._connected = true
      this.reconnectDelay = 1500   // reset backoff on success
      console.log('[AURA-WS] Connected')
      this.emit('connection', { status: 'connected' })
    }

    this.ws.onmessage = (e) => {
      try {
        const { type, data } = JSON.parse(e.data)
        this.emit(type, data)
        this.emit('*', { type, data })
      } catch { /* ignore malformed frames */ }
    }

    this.ws.onclose = () => {
      if (this._connected) {
        this._connected = false
        this.emit('connection', { status: 'disconnected' })
        console.log('[AURA-WS] Disconnected — reconnecting in', this.reconnectDelay, 'ms')
      }
      this._scheduleReconnect()
    }

    this.ws.onerror = () => {
      this.ws?.close()
    }
  }

  private _scheduleReconnect() {
    this._reconnectTimer = setTimeout(() => {
      this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxDelay)
      this.connect()
    }, this.reconnectDelay)
  }

  send(type: string, data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, ...data }))
      return true
    }
    return false
  }

  on(event: string, handler: Handler) {
    if (!this.handlers.has(event)) this.handlers.set(event, [])
    this.handlers.get(event)!.push(handler)
    return () => this.off(event, handler)
  }

  off(event: string, handler: Handler) {
    const handlers = this.handlers.get(event) || []
    this.handlers.set(event, handlers.filter(h => h !== handler))
  }

  private emit(event: string, data: any) {
    ;(this.handlers.get(event) || []).forEach(h => {
      try { h(data) } catch { /* prevent one bad handler killing the bus */ }
    })
  }

  get connected() { return this._connected }
}

export const ws = new AuraWebSocket()
ws.connect()
