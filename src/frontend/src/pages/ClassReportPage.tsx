import { useEffect, useState } from 'react'
import { SessionEndedError } from '../api/sessionEnded'
import type { TeacherClass } from '../api/teacher'
import { getClassReport, getClassReportCsv, type ClassReport } from '../api/teacherReport'
import ClassReportView from '../components/ClassReportView'

interface Props { classroom: TeacherClass; onBack: () => void; onSessionEnded: () => void }

// Makes the browser save the file, as if the teacher clicked a download link.
function saveFile(file: Blob, filename: string) {
  const url = URL.createObjectURL(file)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export default function ClassReportPage({ classroom, onBack, onSessionEnded }: Props) {
  const [report, setReport] = useState<ClassReport | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let active = true
    getClassReport(classroom.id).then((data) => { if (active) setReport(data) }).catch((err) => {
      if (!active) return
      if (err instanceof SessionEndedError) onSessionEnded()
      else setError((err as Error).message)
    })
    return () => { active = false }
  }, [classroom.id, onSessionEnded])

  async function handleDownload() {
    setError('')
    setBusy(true)
    try {
      const { file, filename } = await getClassReportCsv(classroom.id)
      saveFile(file, filename)
    } catch (err) {
      if (err instanceof SessionEndedError) onSessionEnded()
      else setError((err as Error).message)
    } finally { setBusy(false) }
  }

  return <ClassReportView classTitle={classroom.name} report={report} error={error} busy={busy}
    onDownload={handleDownload} onBack={onBack} />
}
