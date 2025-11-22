import { useState, useEffect } from 'react'
import axios from 'axios'
import { API_BASE_URL } from '../config'
import './AdminPortal.css'

function AdminPortal() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showAddUser, setShowAddUser] = useState(false)
  const [showEditUser, setShowEditUser] = useState(false)
  const [showChangePassword, setShowChangePassword] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'readonly'
  })

  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('session_token')
      const response = await axios.get(`${API_BASE_URL}/api/users`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      setUsers(response.data.users)
      setError(null)
    } catch (err) {
      setError('Failed to fetch users. Make sure you have admin access.')
      console.error('Error fetching users:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAddUser = async (e) => {
    e.preventDefault()
    try {
      const token = localStorage.getItem('session_token')
      await axios.post(`${API_BASE_URL}/api/auth/register`, formData, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      setShowAddUser(false)
      setFormData({ username: '', email: '', password: '', role: 'readonly' })
      fetchUsers()
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to create user')
    }
  }

  const handleUpdateUser = async (e) => {
    e.preventDefault()
    try {
      const token = localStorage.getItem('session_token')
      await axios.put(
        `${API_BASE_URL}/api/users/${selectedUser.user_id}`,
        {
          username: formData.username,
          email: formData.email,
          role: formData.role,
          is_active: formData.is_active
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )
      setShowEditUser(false)
      setSelectedUser(null)
      setFormData({ username: '', email: '', password: '', role: 'readonly' })
      fetchUsers()
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to update user')
    }
  }

  const handleChangePassword = async (e) => {
    e.preventDefault()
    try {
      const token = localStorage.getItem('session_token')
      await axios.put(
        `${API_BASE_URL}/api/users/${selectedUser.user_id}/password`,
        { password: formData.password },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )
      setShowChangePassword(false)
      setSelectedUser(null)
      setFormData({ username: '', email: '', password: '', role: 'readonly' })
      alert('Password changed successfully')
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to change password')
    }
  }

  const handleDeleteUser = async (userId, username) => {
    if (!window.confirm(`Are you sure you want to delete user "${username}"?`)) {
      return
    }

    try {
      const token = localStorage.getItem('session_token')
      await axios.delete(`${API_BASE_URL}/api/users/${userId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      fetchUsers()
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to delete user')
    }
  }

  const openEditUser = (user) => {
    setSelectedUser(user)
    setFormData({
      username: user.username,
      email: user.email,
      role: user.role,
      is_active: user.is_active === 1
    })
    setShowEditUser(true)
  }

  const openChangePassword = (user) => {
    setSelectedUser(user)
    setFormData({ username: '', email: '', password: '', role: 'readonly' })
    setShowChangePassword(true)
  }

  if (loading) {
    return <div className="loading">Loading users...</div>
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  return (
    <div className="admin-portal">
      <div className="admin-header">
        <h1>Admin Portal</h1>
        <button className="btn-primary" onClick={() => setShowAddUser(true)}>
          Add New User
        </button>
      </div>

      <div className="users-table-container">
        <table className="users-table">
          <thead>
            <tr>
              <th>Username</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Created</th>
              <th>Last Login</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.user_id}>
                <td>{user.username}</td>
                <td>{user.email}</td>
                <td>
                  <span className={`role-badge role-${user.role}`}>
                    {user.role}
                  </span>
                </td>
                <td>
                  <span className={`status-badge status-${user.is_active ? 'active' : 'inactive'}`}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>{new Date(user.created_at).toLocaleDateString()}</td>
                <td>{user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</td>
                <td className="actions">
                  <button className="btn-edit" onClick={() => openEditUser(user)}>
                    Edit
                  </button>
                  <button className="btn-password" onClick={() => openChangePassword(user)}>
                    Change Password
                  </button>
                  <button className="btn-delete" onClick={() => handleDeleteUser(user.user_id, user.username)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showAddUser && (
        <div className="modal-overlay" onClick={() => setShowAddUser(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Add New User</h2>
            <form onSubmit={handleAddUser}>
              <div className="form-group">
                <label>Username</label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                  minLength="8"
                />
              </div>
              <div className="form-group">
                <label>Role</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                >
                  <option value="readonly">Read Only</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-cancel" onClick={() => setShowAddUser(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showEditUser && (
        <div className="modal-overlay" onClick={() => setShowEditUser(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Edit User</h2>
            <form onSubmit={handleUpdateUser}>
              <div className="form-group">
                <label>Username</label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Role</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                >
                  <option value="readonly">Read Only</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                  {' '}Active
                </label>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-cancel" onClick={() => setShowEditUser(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Update User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showChangePassword && (
        <div className="modal-overlay" onClick={() => setShowChangePassword(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Change Password for {selectedUser?.username}</h2>
            <form onSubmit={handleChangePassword}>
              <div className="form-group">
                <label>New Password</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                  minLength="8"
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-cancel" onClick={() => setShowChangePassword(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Change Password
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default AdminPortal
