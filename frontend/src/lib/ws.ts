type Handler = (data: any) => void

class AuraWebSocket {
  private ws: WebSocket | null = null
  private handlers: Map<string, Handler[]> = new Map()
  private reconnectDelay = 2000
  private _connected = false

  connect() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${proto}://${location.host}/ws`
    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      this._connected = true
      console.log('[AURA-WS] Connected')
      this.emit('connection', { status: 'connected' })
    }

    this.ws.onmessage = (e) => {
      try {
        const { type, data } = JSON.parse(e.data)
        this.emit(type, data)
        this.emit('*', { type, data })
      } catch {}
    }

    this.ws.onclose = () => {
      this._connected = false
      this.emit('connection', { status: 'disconnected' })
      setTimeout(() => this.connect(), this.reconnectDelay)
    }

    this.ws.onerror = () => {
      this.ws?.close()
    }
  }

  send(type: string, data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, ...data }))
    }
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
    ;(this.handlers.get(event) || []).forEach(h => h(data))
  }

  get connected() { return this._connected }
}

export const ws = new AuraWebSocket()
ws.connect()
