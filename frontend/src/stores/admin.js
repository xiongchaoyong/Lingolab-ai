import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getMyClassesApi, createClassApi, getClassStudentsApi, joinClassApi,
  getAssignmentsApi, createAssignmentApi, getSubmissionsApi, reviewSubmissionApi,
  getUsersApi, setUserStatusApi, getDashboardApi,
} from '@/api/admin'

export const useAdminStore = defineStore('admin', () => {
  // ===== 班级 =====
  const classes = ref([])
  const students = ref([])

  async function fetchClasses() {
    const res = await getMyClassesApi()
    classes.value = res.classes || []
  }

  async function createClass(data) {
    await createClassApi(data)
    await fetchClasses()
  }

  async function fetchStudents(classId) {
    const res = await getClassStudentsApi(classId)
    students.value = res.students || []
  }

  async function joinClass(inviteCode) {
    const res = await joinClassApi(inviteCode)
    return res
  }

  // ===== 作业 =====
  const assignments = ref([])
  const submissions = ref([])

  async function fetchAssignments() {
    const res = await getAssignmentsApi()
    assignments.value = res.assignments || []
  }

  async function createAssignment(data) {
    await createAssignmentApi(data)
    await fetchAssignments()
  }

  async function fetchSubmissions(assignmentId) {
    const res = await getSubmissionsApi(assignmentId)
    submissions.value = res.submissions || []
  }

  async function reviewSubmission(submissionId, data) {
    await reviewSubmissionApi(submissionId, data)
  }

  // ===== 用户管理 =====
  const users = ref([])
  const userTotal = ref(0)

  async function fetchUsers(params = {}) {
    const res = await getUsersApi(params)
    users.value = res.users || []
    userTotal.value = res.total || 0
  }

  async function setUserStatus(userId, isActive) {
    await setUserStatusApi(userId, isActive)
  }

  // ===== 仪表盘 =====
  const dashboard = ref(null)

  async function fetchDashboard() {
    const res = await getDashboardApi()
    dashboard.value = res
  }

  return {
    classes, students, fetchClasses, createClass, fetchStudents, joinClass,
    assignments, submissions, fetchAssignments, createAssignment, fetchSubmissions, reviewSubmission,
    users, userTotal, fetchUsers, setUserStatus,
    dashboard, fetchDashboard,
  }
})