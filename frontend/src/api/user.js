import api from './client';

const userApi = {
  getProfile: () => api.get('/users/profile'),
  updateProfile: (data) => api.put('/users/profile', data),
  getAddresses: () => api.get('/users/addresses'),
  addAddress: (data) => api.post('/users/addresses', data),
  updateAddress: (id, data) => api.put(`/users/addresses/${id}`, data),
  deleteAddress: (id) => api.delete(`/users/addresses/${id}`),
  setDefaultAddress: (id) => api.put(`/users/addresses/${id}/default`),
  getConsents: () => api.get('/user/consents'),
  updateConsents: (data) => api.put('/user/consents', data),
  requestDeletion: () => api.post('/user/delete-account'),
  cancelDeletion: () => api.post('/user/cancel-deletion'),
  exportData: () => api.get('/user/data-export'),
};

export default userApi;
