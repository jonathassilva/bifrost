import { useRef } from 'react'

export function UploadZone({ loadedFiles, onAddFiles, onRemoveFile }) {
  const inputRef = useRef()

  const handleChange = (e) => {
    onAddFiles(Array.from(e.target.files))
    e.target.value = ''
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const files = Array.from(e.dataTransfer.files).filter((f) =>
      f.name.endsWith('.csv')
    )
    onAddFiles(files)
  }

  return (
    <div className="mb-6">
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => inputRef.current.click()}
        className="border border-dashed border-zinc-700 hover:border-zinc-500 rounded-xl p-6 text-center cursor-pointer transition-colors group"
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          multiple
          className="hidden"
          onChange={handleChange}
        />
        <div className="text-2xl mb-2">📂</div>
        <p className="text-sm text-zinc-400 group-hover:text-zinc-200 transition-colors">
          Clique ou arraste arquivos <span className="font-mono text-zinc-300">.csv</span> aqui
        </p>
        <p className="text-xs text-zinc-600 mt-1">
          Múltiplos arquivos são suportados — dados consolidados automaticamente
        </p>
      </div>

      {loadedFiles.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-3">
          {loadedFiles.map((f) => (
            <span key={f.name} className="tag">
              <span className="text-zinc-500">📄</span>
              {f.name}
              <button
                onClick={() => onRemoveFile(f.name)}
                className="ml-1 text-zinc-500 hover:text-red-400 transition-colors leading-none"
                title="Remover"
              >
                ✕
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
