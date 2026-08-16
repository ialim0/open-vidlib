declare module 'lucide-react' {
  import * as React from 'react'
  export interface LucideProps extends React.SVGProps<SVGSVGElement> {
    size?: string | number
    color?: string
    strokeWidth?: string | number
    className?: string
  }
  export type LucideIcon = React.FC<LucideProps>
  
  const icon: LucideIcon
  export default icon
  export const Search: LucideIcon
  export const Video: LucideIcon
  export const ArrowRight: LucideIcon
  export const ArrowLeft: LucideIcon
  export const Sparkles: LucideIcon
  export const Play: LucideIcon
  export const Pause: LucideIcon
  export const Clock: LucideIcon
  export const BookOpen: LucideIcon
  export const Database: LucideIcon
  export const Globe: LucideIcon
  export const CheckCircle2: LucideIcon
  export const Send: LucideIcon
  export const Loader2: LucideIcon
  export const X: LucideIcon
  export const Trophy: LucideIcon
  export const ChevronRight: LucideIcon
  export const ChevronDown: LucideIcon
  export const ChevronUp: LucideIcon
  export const Volume2: LucideIcon
  export const HelpCircle: LucideIcon
  export const CheckIcon: LucideIcon
  export const ChevronRightIcon: LucideIcon
  export const CircleIcon: LucideIcon
  export const NotebookPen: LucideIcon
  export const Mic: LucideIcon
  export const Bold: LucideIcon
  export const Italic: LucideIcon
  export const Underline: LucideIcon
  export const List: LucideIcon
  export const Link: LucideIcon
  export const AlignCenter: LucideIcon
  export const AlignJustify: LucideIcon
  export const ListOrdered: LucideIcon
  export const Users: LucideIcon
  export const Library: LucideIcon
  export const GraduationCap: LucideIcon
}
