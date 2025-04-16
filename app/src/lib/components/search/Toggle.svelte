  <div class="toggle-button-container">
      <div class="btn btn-pill" id="button-1">
        <input type="checkbox" class="checkbox" />
        <div class="knob"></div>
        <div class="btn-bg"></div>
      </div>
</div>
  <style>

.toggle-button-container {
  display: flex;

}

.knob,
.btn-bg {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
}

.btn {
  position: relative;
  top: 50%;
  width: 90px;
  height: 36px;
  margin: -20px auto 0 auto;
  overflow: hidden;
  /* box-shadow: none; */
}

.btn.btn-pill,
.btn.btn-pill > .btn-bg {
  border-radius: var(--radius-3);
}

.checkbox {
  position: relative;
  width: 100%;
  height: 100%;
  padding: 0;
  margin: 0;
  opacity: 0;
  cursor: pointer;
  z-index: 3;
}

.knob {
  z-index: 2;
}

.btn-bg {
  width: 100%;
  background-color: #ebf7fc;
  transition: 0.3s ease all;
  z-index: 1;
}

/* Button 1 */
#button-1 .knob:before {
  content: "Sematic";
  position: absolute;
  top: 10px;
  left: 18px;
  width: var(--size-2);
  height: 10px;
  color: var(--text-2-light);
  font-size: 12px;
  font-weight: 400;
  text-align: center;
  line-height: 1;
  /* background-color: #03a9f4; */
  border-radius: var(--radius-2);
  transition: 0.3s cubic-bezier(0.18, 0.89, 0.35, 1.15) all;
}

#button-1 .checkbox:checked + .knob:before {
  content: "Lexical";
  left: 18px;
}

#button-1 .checkbox:checked ~ .btn-bg {
  background-color: #fcebeb;
}

#button-1 .knob,
#button-1 .knob:before,
#button-1 .btn-bg {
  transition: 0.3s ease all;
}
    
  </style>
