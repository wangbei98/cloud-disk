<template>
  <div>
    <!-- <nav-header></nav-header> -->
	<v-head></v-head>
    <b-container>
      <b-row align-h="center" class="mt-5">
        <b-col cols="5">
          <b-card class="p-3">
            <h3 class="mb-4">Login</h3>
            <b-form @submit="onSubmit" @reset="onReset" v-if="show">
              <b-form-group
                id="input-group-1"
                label="Email address:"
                label-for="input-1"
              >
                <b-form-input
                  id="input-1"
                  v-model="form.email"
                  type="email"
                  required
                  placeholder="Enter email"
                ></b-form-input>
              </b-form-group>

              <b-form-group id="input-group-2" label="Password" label-for="input-2">
                <b-form-input
                  id="input-2"
                  type="password"
                  v-model="form.password"
                  required
                  placeholder="Enter Password"
                ></b-form-input>
              </b-form-group>

              <b-form-group id="input-group-4">
                <b-form-checkbox-group v-model="form.checked" id="checkboxes-4">
                  <b-form-checkbox value="remember">Remenber me</b-form-checkbox>
                </b-form-checkbox-group>
              </b-form-group>
              <div class="d-flex justify-content-between">
                <div>
                  <b-button type="submit" variant="primary">Submit</b-button>&nbsp;
                  <b-button type="reset" variant="danger">Reset</b-button>
                </div>
                <div>
                  <router-link :to="{name: 'Register'}">Register</router-link>
                </div>
              </div>
            </b-form>
          </b-card>
        </b-col>
      </b-row>
    </b-container>
  </div>
</template>

<script>
  import NavHeader from '../common/NavHeader.vue'
  import vHead from '../common/Header.vue'

  export default{
    name:'login',
    components:{
      vHead,
      NavHeader
    },
    data() {
      return {
        form: {
          email: '',
          password: '',
          checked: []
        },
        show: true
      }
    },
    methods:{
      onSubmit(evt) {
        evt.preventDefault()
        this.$store.dispatch('login',{
          email:this.form.email,
          password:this.form.password
        }).then(response => {
          this.$store.dispatch('saveToken',token)
          // 如果登录成功，则跳转到文件页
          this.$router.push('/home/files/-1')

          const token = this.$cookie.get('token')
          this.$store.dispatch('saveToken',token)

          //拉取所有文件信息
          this.$store.dispatch('getAllFiles')
        })
      },
      onReset(evt) {
        evt.preventDefault()
        // Reset our form values
        this.form.email = ''
        this.form.password = ''
        this.form.checked = []
        // Trick to reset/clear native browser form validation state
        this.show = false
        this.$nextTick(() => {
          this.show = true
        })
      }
    }
  }
</script>

<style>
  body {
    background: #eef1f4;
  }
</style>
